import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const now = new Date().toISOString();

const statusDir = '_status';
mkdirSync(statusDir, { recursive: true });
const file = join(statusDir, 'ping.txt');
writeFileSync(file, `Ping at ${now}\n`);

console.log(`Ping written to ${file}`);

async function sendToNotion() {
  const token = process.env.NOTION_API_KEY;
  const databaseId = process.env.NOTION_DATABASE_ID;
  if (!token || !databaseId) {
    console.log('Notion env vars missing, skipping Notion sync');
    return;
  }

  const res = await fetch('https://api.notion.com/v1/pages', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      parent: { database_id: databaseId },
      properties: {
        Name: {
          title: [{ text: { content: `Ping ${now}` } }]
        }
      }
    })
  });

  if (!res.ok) {
    console.error('Failed to sync to Notion:', await res.text());
  } else {
    console.log('Synced to Notion');
  }
}

sendToNotion().catch(err => {
  console.error('Notion request error', err);
});
