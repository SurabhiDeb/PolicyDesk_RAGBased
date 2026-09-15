const fs = require('fs');
const path = require('path');

function build(version) {
  const file = path.join(__dirname, '..', 'products', 'triage', 'prompts', `${version}.md`);
  return ({ vars }) => [
    { role: 'system', content: fs.readFileSync(file, 'utf8') },
    { role: 'user', content: vars.message },
  ];
}

module.exports = { v1: build('v1'), v2: build('v2') };