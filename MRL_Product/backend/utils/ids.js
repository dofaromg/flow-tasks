'use strict';
const { randomUUID, randomBytes } = require('crypto');

exports.uuid = () => randomUUID();
exports.token = (len = 32) => randomBytes(len).toString('hex');
exports.shortId = () => randomBytes(6).toString('hex');
