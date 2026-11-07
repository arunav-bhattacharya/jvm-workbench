# Track: io, "NIO and event loops" (lab: labs/nio, package workbench.nio.lNN)

Research notes: "research_notes/Advanced JVM runtime topics/nio_event_loops.md". The lab module has Netty 4.2.20.Final (netty-all) and
Vert.x core 5.2.3. Network tests use localhost on ephemeral ports with short timeouts; prefer
Netty's EmbeddedChannel where possible. Link to vt-01..vt-06 (virtual threads) and rx-06 (schedulers).

Lessons:
- io-01 Blocking IO, threads and the C10K problem: thread-per-connection, what a blocked read costs,
  Little's law again. Lab: a blocking echo server and a test that shows N clients need N threads.
- io-02 NIO: ByteBuffer flip/compact, channels, Selector, interest/ready sets, partial reads and
  writes, OP_WRITE. Lab: an NIO echo server that handles partial reads.
- io-03 Netty: EventLoopGroup and the single event-loop thread, Channel, ChannelPipeline, inbound and
  outbound handlers, ByteBuf reference counting and leak detection, Netty 4.2's IoHandler-based groups.
  Lab: a decoder and handler pipeline tested with EmbeddedChannel; catch a ByteBuf leak.
- io-04 Vert.x and Quarkus: the event loop golden rule, blocked-thread warnings (real text from the
  notes), executeBlocking and workers, Quarkus REST threading (@Blocking, @NonBlocking,
  @RunOnVirtualThread). Lab: find and fix a handler that blocks the event loop.
- io-05 Zero-copy, epoll, io_uring, and where virtual threads fit: transferTo/sendfile, FileRegion,
  how a virtual thread's blocking read parks on the JDK poller, and a decision guide.
