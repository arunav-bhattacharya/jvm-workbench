# Track: io, "Servers and event loops: NIO, Netty, Vert.x and Jetty" (lab: labs/nio, package workbench.nio.lNN)

Research notes: "research_notes/Advanced JVM runtime topics/nio_event_loops.md" and "research_notes/Advanced JVM runtime topics/jetty_netty_vertx_depth.md" (Jetty 12, Netty
codecs and flow control, Vert.x verticles/contexts/event bus). Both were built from runs on JDK 21
with Netty 4.2.20.Final, Vert.x 5.2.3 and Quarkus 3.40.1: reuse their observed outputs and numbers.
The lab module has netty-all 4.2.20.Final, vertx-core and vertx-web 5.2.3, jetty-server 12.1.14, and
vertx-junit5 for tests. Network tests use localhost on ephemeral ports with short timeouts; prefer
Netty's EmbeddedChannel and Vert.x's VertxTestContext. Use Netty 4.2 APIs (MultiThreadIoEventLoopGroup
with NioIoHandler.newFactory(); not the deprecated NioEventLoopGroup or addLast(EventExecutorGroup, ...)),
and Vert.x 5's futures-only API. Link to vt-01..vt-06 (virtual threads), exec-03 (sizing) and rx-06.

Lessons:
- io-01 Blocking IO, threads and the C10K problem: thread-per-connection, what a blocked read costs,
  Little's law again. Lab: a blocking echo server; a test shows N clients need N threads.
- io-02 NIO: ByteBuffer flip/compact, channels, Selector, interest/ready sets, partial reads and
  writes, the OP_WRITE busy-spin (0 vs ~94,000 wakeups in the notes). Lab: an NIO echo server that
  handles partial reads and only registers OP_WRITE while it has pending bytes.
- io-03 Netty: event loop groups and the single event-loop thread, Channel, ChannelPipeline, inbound
  and outbound handlers, Netty 4.2's IoHandler-based groups, never blocking the loop (hand work to
  your own executor and write back with ctx.writeAndFlush). Lab: a pipeline tested with EmbeddedChannel.
- io-04 Netty in practice: codecs (ByteToMessageDecoder, LengthFieldBasedFrameDecoder, encoders),
  flow control (isWritable, water marks, AUTO_READ toward a slow consumer), ByteBuf pooling and
  reference counting, leak detection in PARANOID mode with the leak listener. Lab: a length-prefixed
  payment-message codec plus a leak caught in a test.
- io-05 Vert.x: event loops, verticles and deployment, contexts (event loop, worker, virtual thread
  in Vert.x 5), the event bus, the golden rule and the exact blocked-thread warning, executeBlocking
  and its ordered default (the 2,814 / 2,043 / 576 ms measurements). Lab: a verticle with event-bus
  request/reply tested with vertx-junit5, then fix one that blocks the loop.
- io-06 Quarkus on Vert.x: how the return type picks the thread (Uni/Multi/CompletionStage/suspend on
  the IO thread, the rest on workers), @Blocking/@NonBlocking, @RunOnVirtualThread, what happens when
  you block the IO thread (warning, BlockingOperationNotAllowedException), event-loop count defaults.
  Pin statements to Quarkus 3.40 and recommend explicit @Blocking where the docs disagree. The lab
  simulates the dispatch rules with plain Vert.x (no Quarkus dependency).
- io-07 Jetty 12: connectors and acceptors, ManagedSelector, the core Handler API vs the Servlet
  environments, QueuedThreadPool and reserved threads, the adaptive execution strategy, virtual
  threads in Jetty 12, and how Jetty compares with Netty-based servers and Tomcat. Lab: a Jetty core
  Handler server (started on port 0 in tests) with a blocking endpoint moved to virtual threads.
- io-08 Zero-copy, epoll, io_uring, and choosing a server model: transferTo/sendfile (the strace
  numbers in the notes), Netty FileRegion, io_uring status (no promise that it is faster), how a
  virtual thread's blocking read parks on the JDK poller (JDK 21 vs 22+), and a decision table:
  thread-per-request on virtual threads vs event loops (Netty/Vert.x) vs Jetty for a payments team.
