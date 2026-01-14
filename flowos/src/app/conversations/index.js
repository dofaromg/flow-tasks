"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConversationManager = void 0;
const utils_1 = require("../../utils");
class ConversationManager {
    constructor(storage) {
        this.storage = storage;
    }
    startConversation(context) {
        const thread = {
            id: (0, utils_1.randomId)(),
            messages: [],
            persona: context.persona,
            project: context.project,
            createdAt: (0, utils_1.now)(),
        };
        return this.storage.upsertConversation(thread);
    }
    appendMessage(threadId, author, content, context) {
        const thread = this.storage.getConversation(threadId);
        if (!thread) {
            throw new Error(`Conversation ${threadId} not found`);
        }
        const message = {
            id: (0, utils_1.randomId)(),
            author,
            content,
            createdAt: (0, utils_1.now)(),
            context,
        };
        const updated = { ...thread, messages: [...thread.messages, message] };
        return this.storage.upsertConversation(updated);
    }
    list() {
        return this.storage.listConversations();
    }
}
exports.ConversationManager = ConversationManager;
