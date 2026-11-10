const fs = require('fs');

module.exports = {
  viewportWidth: 1366,
  viewportHeight: 800,
  video: false,
  retries: { runMode: 1, openMode: 0 },
  defaultCommandTimeout: 8000,
  downloadsFolder: 'cypress/downloads',
  e2e: {
    baseUrl: 'http://127.0.0.1:8001',
    setupNodeEvents(on, config) {
      on('task', {
        readCsv(filePath) {
          if (fs.existsSync(filePath)) {
            return fs.readFileSync(filePath, 'utf8');
          }
          return null;
        },
        log(message) {
          console.log(message);
          return null;
        },
      });
    },
  },
};
