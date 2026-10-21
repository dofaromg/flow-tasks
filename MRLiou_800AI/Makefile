.PHONY: install verify test run package
install:
	./scripts/install.sh
verify:
	./scripts/verify.sh
test:
	python -m unittest discover -s tests -v
run:
	python -m mrliou_800ai.cli serve --host 127.0.0.1 --port 8787
package:
	./scripts/package.sh
