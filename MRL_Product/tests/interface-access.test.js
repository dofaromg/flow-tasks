'use strict';
// origin_signature: MrLiouWord
const test = require('node:test');
const assert = require('node:assert/strict');
const { ownsAnalysis, ownsOrder } = require('../backend/modules/access');

test('reject missing record', () => assert.equal(ownsAnalysis(null, 's1', null), false));
test('reject empty credentials', () => assert.equal(ownsAnalysis({session_id:'s1'}, '', null), false));
test('permit same session', () => assert.equal(ownsAnalysis({session_id:'s1',user_id:null}, 's1', null), true));
test('reject other session', () => assert.equal(ownsAnalysis({session_id:'s1',user_id:null}, 's2', null), false));
test('permit same verified user', () => assert.equal(ownsAnalysis({session_id:'s1',user_id:'u1'}, 's2', 'u1'), true));
test('reject mismatched verified user', () => assert.equal(ownsAnalysis({session_id:'s1',user_id:'u1'}, 's2', 'u2'), false));
test('orders share ownership check', () => assert.equal(ownsOrder({session_id:'s1',user_id:'u1'}, 's2', 'u2'), false));
