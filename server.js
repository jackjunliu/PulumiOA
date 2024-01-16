'use strict';

const express = require('express');

// Constants
const PORT = 8080;
const HOST = '0.0.0.0';
let config = new pulumi.Config();
let configValue = config.require("configValue");
//console.log(`Message: ${config.pulumiOA:message}`);

// App
const app = express();
app.get('/', (req, res) => {
  res.send('Hello World' + ${config.pulumiOA:message});
});

app.listen(PORT, HOST);
console.log(`Running on http://${HOST}:${PORT}`);