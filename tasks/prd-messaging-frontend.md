# PRD: Messaging Frontend for Covered Call Strategist

## Introduction/Overview

The Covered Call Strategist agent currently works via CLI. This feature adds a messaging frontend so users can interact with the agent through Telegram and WhatsApp on any device (smartphone or PC).

**Problem:** Users need to be at a terminal to use the agent, limiting accessibility and convenience.

**Solution:** Deploy the agent as a messaging bot, starting with Telegram (simpler API) and adding WhatsApp support later.

## Goals

1. Enable users to access the covered call strategist from any device via messaging apps
2. Start with Telegram bot, then expand to WhatsApp
3. Maintain conversation history per user for context-aware interactions
4. Implement allowlist-based access control for authorized users only
5. Deploy as serverless functions for cost-efficiency and scalability

## User Stories

1. **As an authorized user**, I want to message the bot on Telegram with "AAPL 500 shares" and receive a covered call recommendation, so I can get trading advice on my phone.

2. **As an authorized user**, I want the bot to remember my previous analyses, so I can ask follow-up questions like "what about a more conservative strike?"

3. **As an admin**, I want to add/remove users from the allowlist, so I can control who has access to the bot.

4. **As an authorized user**, I want to receive the same quality recommendations on WhatsApp as Telegram, so I can use my preferred messaging app.

5. **As a user**, I want clear error messages if I'm rate-limited, so I understand why my request wasn't processed.

## Functional Requirements

### Phase 1: Telegram Bot

1. **Bot Registration**: Create a Telegram bot via BotFather with appropriate name and description.

2. **Message Handling**: The bot must receive text messages and pass them to the existing `run_covered_call_strategy` tool.

3. **Response Formatting**: The bot must format the agent's response appropriately for Telegram (Markdown support, message length limits).

4. **Allowlist Authentication**:
   - 4.1. Maintain a list of authorized Telegram user IDs or usernames.
   - 4.2. Reject messages from non-allowlisted users with a polite message.
   - 4.3. Provide a mechanism to add/remove users from the allowlist (environment variable or config file).

5. **Persistent Conversation History**:
   - 5.1. Store conversation history per user in a database (DynamoDB, Firestore, or similar).
   - 5.2. Retrieve user's history when processing new messages for context.
   - 5.3. Limit history to last N messages (e.g., 20) to manage storage and context window.

6. **Rate Limiting**:
   - 6.1. Limit users to maximum 10 requests per minute.
   - 6.2. Return a friendly message when rate limit is exceeded.
   - 6.3. Use sliding window or token bucket algorithm.

7. **Serverless Deployment**:
   - 7.1. Deploy as AWS Lambda or Google Cloud Function.
   - 7.2. Use webhook mode (not polling) for Telegram updates.
   - 7.3. Configure appropriate timeouts (agent may take 10-30 seconds).

8. **Error Handling**:
   - 8.1. Catch and log errors gracefully.
   - 8.2. Return user-friendly error messages.
   - 8.3. Implement retry logic for transient failures.

### Phase 2: WhatsApp Integration

9. **WhatsApp Business API Setup**:
   - 9.1. Register for Meta Business API access.
   - 9.2. Set up WhatsApp Business account and phone number.
   - 9.3. Configure webhook for incoming messages.

10. **Unified Message Handler**:
    - 10.1. Abstract message handling to support both platforms.
    - 10.2. Normalize incoming message format from both platforms.
    - 10.3. Format outgoing messages appropriately per platform.

11. **Shared Infrastructure**:
    - 11.1. Use same database for conversation history across platforms.
    - 11.2. Use same allowlist (keyed by platform + user ID).
    - 11.3. Apply same rate limiting rules.

## Non-Goals (Out of Scope)

- **Payment/subscription system** - All authorized users have equal access
- **Voice message support** - Text only for initial release
- **Image/file attachments** - No chart generation or file sharing
- **Group chat support** - Direct messages only
- **Multi-language support** - English only
- **Mobile app development** - Using existing messaging apps only
- **Real-time price alerts** - On-demand queries only

## Technical Considerations

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐
│  Telegram   │────▶│   Lambda/   │────▶│  Covered Call    │
│  Webhook    │     │   Cloud Fn  │     │  Strategy Agent  │
└─────────────┘     └──────┬──────┘     └──────────────────┘
                           │
┌─────────────┐            │            ┌──────────────────┐
│  WhatsApp   │────────────┤            │   DynamoDB/      │
│  Webhook    │            └───────────▶│   Firestore      │
└─────────────┘                         │  (History + Auth)│
                                        └──────────────────┘
```

### Dependencies

- **Telegram**: `python-telegram-bot` or `aiogram` library
- **WhatsApp**: Meta Cloud API / WhatsApp Business API
- **Database**: AWS DynamoDB (if Lambda) or Google Firestore (if Cloud Functions)
- **Existing**: `google-adk`, `yfinance`, current agent code

### Constraints

1. **Telegram message limit**: 4096 characters - may need to split long responses
2. **WhatsApp API approval**: May take days/weeks for Meta approval
3. **Cold starts**: Serverless functions may have latency on first request
4. **Timeout limits**: Lambda (15 min max), Cloud Functions (9 min max) - should be sufficient
5. **Cost**: Pay-per-invocation model - monitor usage

### Recommended Stack

| Component | Recommendation |
|-----------|----------------|
| Cloud Provider | AWS (Lambda + DynamoDB) or GCP (Cloud Functions + Firestore) |
| Telegram Library | `python-telegram-bot` v20+ (async support) |
| WhatsApp | Meta Cloud API with `requests` or `httpx` |
| Rate Limiting | Redis (AWS ElastiCache) or in-memory with DynamoDB backing |

## Success Metrics

1. **Availability**: Bot responds to 99% of messages within 60 seconds
2. **Adoption**: At least 5 active users within first month
3. **Reliability**: Less than 1% error rate on valid requests
4. **User satisfaction**: Users can complete full analysis workflows via chat
5. **Platform parity**: WhatsApp users get identical functionality to Telegram users

## Decisions Made

1. **Cloud Provider**: GCP (Cloud Functions + Firestore)

2. **Allowlist Management**: Database table in Firestore (phone numbers, dynamic updates without redeploy)

3. **Platform Rollout**: Telegram first, WhatsApp only after Telegram is stable and working

## Open Questions

1. **Message formatting**: Should we use plain text or rich formatting (Markdown/HTML) for responses?

2. **History retention**: How long should conversation history be retained per user? (7 days, 30 days, indefinitely?)

---

*Generated: 2026-01-04*
