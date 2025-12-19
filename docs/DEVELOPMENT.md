##DEVELOPMENT.md
## Development Notes

### Day 1 (2 hours)
- Started with architecture design
- Chose Azure because I have experience with it
- Debated between monolith vs microservices, went with microservices
  for better scalability even though it's more complex

### Day 2 (2.5 hours)
- Implemented base tool interface
- Had issues with async/await - forgot to use asyncio.run()
- Added retry logic after testing showed DuckDuckGo API can be flaky
- Struggled with type hints for tool results - settled on 'any' for now

### What I'd improve with more time:
- Real LLM integration (currently using keyword matching)
- Better error messages
- More comprehensive tests for edge cases