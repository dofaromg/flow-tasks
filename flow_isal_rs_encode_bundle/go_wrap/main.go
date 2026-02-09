package main

import (
	"bytes"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"time"

	"github.com/zeebo/blake3"
)

type Manifest struct {
	K         int      `json:"k"`
	M         int      `json:"m"`
	W         int      `json:"w"`
	ShardSize int64    `json:"shard_size"`
	InputSize int64    `json:"input_size"`
	InputB3   string   `json:"input_blake3"`
	Data      []string `json:"data_shards"`
	Parity    []string `json:"parity_shards"`
}

type Trace struct {
	EventID    string `json:"event_id"`
	RID        string `json:"rid"`
	Tick       int64  `json:"tick"`
	PersonaID  string `json:"persona_id"`
	MerkleRoot string `json:"merkle_root"`
}

func b3File(path string) (string, int64, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", 0, err
	}
	defer f.Close()

	h := blake3.New()
	n, err := io.Copy(h, f)
	if err != nil {
		return "", 0, err
	}
	return hex.EncodeToString(h.Sum(nil)), n, nil
}

func writeFile(path string, b []byte) error {
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return err
	}
	return os.WriteFile(path, b, 0644)
}

func splitToKShards(inPath, dataDir string, k int) (shardSize int64, inputSize int64, shardPaths []string, err error) {
	b, err := os.ReadFile(inPath)
	if err != nil {
		return 0, 0, nil, err
	}
	inputSize = int64(len(b))

	// shardSize = ceil(len/k)
	ss := (len(b) + k - 1) / k
	shardSize = int64(ss)

	shardPaths = make([]string, 0, k)
	if err := os.MkdirAll(dataDir, 0755); err != nil {
		return 0, 0, nil, err
	}

	for i := 0; i < k; i++ {
		start := i * ss
		end := start + ss
		if start > len(b) {
			start = len(b)
		}
		if end > len(b) {
			end = len(b)
		}
		chunk := make([]byte, ss)
		copy(chunk, b[start:end])

		p := filepath.Join(dataDir, fmt.Sprintf("shard_%02d.bin", i))
		if err := os.WriteFile(p, chunk, 0644); err != nil {
			return 0, 0, nil, err
		}
		shardPaths = append(shardPaths, p)
	}
	return shardSize, inputSize, shardPaths, nil
}

func randID(n int) string {
	b := make([]byte, n)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}

func merkleDir(dir string) (string, error) {
	// deterministic sha256 fold implemented with system sha256sum for parity with scripts/merkle_dir.sh
	cmd := exec.Command("bash", "-lc", fmt.Sprintf(`cd %q && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}'`, dir))
	out, err := cmd.Output()
	if err != nil {
		return "", err
	}
	return string(bytes.TrimSpace(out)), nil
}

func listFiles(dir string) ([]string, error) {
	var files []string
	err := filepath.Walk(dir, func(p string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if info.Mode().IsRegular() {
			files = append(files, p)
		}
		return nil
	})
	if err != nil {
		return nil, err
	}
	sort.Strings(files)
	return files, nil
}

func main() {
	in := flag.String("in", "", "input file")
	outDir := flag.String("out", "out", "output dir")
	k := flag.Int("k", 4, "data shards")
	m := flag.Int("m", 2, "parity shards")
	w := flag.Int("w", 8, "GF width (only 8 supported in C encoder)")
	persona := flag.String("persona", "partner_persona", "persona_id for trace")
	flag.Parse()

	if *in == "" {
		fmt.Fprintln(os.Stderr, "missing --in")
		os.Exit(2)
	}

	// Paths
	dataDir := filepath.Join(*outDir, "data")
	parityDir := filepath.Join(*outDir, "parity")
	if err := os.MkdirAll(parityDir, 0755); err != nil {
		panic(err)
	}

	// Split input into k data shards
	shardSize, inputSize, dataShards, err := splitToKShards(*in, dataDir, *k)
	if err != nil {
		panic(err)
	}

	// Call ISA-L encoder
	encBin := filepath.Join("..", "bin", "isal_rs_encode")
	if _, err := os.Stat(encBin); err != nil {
		// try relative to cwd if launched from repo root
		encBin = filepath.Join("bin", "isal_rs_encode")
	}

	cmd := exec.Command(encBin,
		"--k", fmt.Sprint(*k),
		"--m", fmt.Sprint(*m),
		"--w", fmt.Sprint(*w),
		"--size", fmt.Sprint(shardSize),
		"--in", dataDir,
		"--out", parityDir,
	)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		panic(err)
	}

	// Build manifest
	inputHash, _, err := b3File(*in)
	if err != nil {
		panic(err)
	}

	parityShards := make([]string, 0, *m)
	for j := 0; j < *m; j++ {
		parityShards = append(parityShards, filepath.Join(parityDir, fmt.Sprintf("shard_%02d.bin", *k+j)))
	}

	man := Manifest{
		K:         *k,
		M:         *m,
		W:         *w,
		ShardSize: shardSize,
		InputSize: inputSize,
		InputB3:   inputHash,
		Data:      dataShards,
		Parity:    parityShards,
	}
	mb, _ := json.MarshalIndent(man, "", "  ")
	if err := writeFile(filepath.Join(*outDir, "manifest.json"), mb); err != nil {
		panic(err)
	}

	// Trace + merkle_root
	mr, err := merkleDir(*outDir)
	if err != nil {
		panic(err)
	}
	t := Trace{
		EventID:    randID(8),
		RID:        randID(8),
		Tick:       time.Now().UnixNano(),
		PersonaID:  *persona,
		MerkleRoot: mr,
	}
	tb, _ := json.MarshalIndent(t, "", "  ")
	if err := writeFile(filepath.Join(*outDir, "trace.json"), tb); err != nil {
		panic(err)
	}

	// Also write .merkle_root for parity with your workflow
	if err := writeFile(filepath.Join(*outDir, ".merkle_root"), []byte(mr+"\n")); err != nil {
		panic(err)
	}

	// quick listing output (deterministic)
	files, _ := listFiles(*outDir)
	fmt.Println("OK output files:")
	for _, f := range files {
		fmt.Println(" -", f)
	}
}
