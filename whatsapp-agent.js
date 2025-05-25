const { create, Client } = require('@open-wa/wa-automate');

create({
  sessionId: "AR_Glasses",
  multiDevice: true
}).then(client => start(client));

function start(client) {
  console.log("WhatsApp client started");

  process.stdin.on('data', async (data) => {
    try {
      const input = data.toString().trim();
      const { number, message } = JSON.parse(input);
      await client.sendText(number + '@c.us', message);
      console.log("SENT");
    } catch (err) {
      console.error("ERROR", err);
    }
  });
}