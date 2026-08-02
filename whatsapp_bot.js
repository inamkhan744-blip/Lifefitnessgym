const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        executablePath: 'google-chrome-stable', // <--- YEH LINE ADD KAREIN
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
    }
});

client.on('qr', (qr) => {
    qrcode.generate(qr, { small: true });
    console.log('📱 Scan this QR code with WhatsApp:');
});

client.on('ready', () => {
    console.log('✅ WhatsApp Bot is ready!');
    console.log('📋 Now you can add members to groups!');
});

client.on('message', message => {
    console.log(`📩 Message from ${message.from}: ${message.body}`);
});

client.initialize();