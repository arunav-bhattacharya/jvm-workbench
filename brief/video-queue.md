# Video queue, most important first

Batch done (28 live, the last 4 conc/jmm ones still rendering): the 8 fp lessons, then conc-02, jmm-03, conc-10, conc-12, exec-03, rx-02, vt-05, exec-05,
co-06, rx-06, co-08, co-09, gen-01, kt-04, pat-06, io-07, pat-07, cls-02, pat-09, pat-08, mem-02, mem-05, mem-03, cls-07.

All three tiers are done: tier 1 and tier 2 (16 live each), tier 3 wave 1 (16 live) and wave 2, the last 6
capstone lessons (6 live). Every lesson in the queue now has a video.

The order: Tier 1 is a mechanism that is hard to picture from text; tier 2 helps but less;
tier 3 is mostly API, reference or project steps, where a video adds the least.

Tier 1
1. conc-04 synchronized and intrinsic locks: the monitor, entry set, reentrancy
2. vt-01 the thread-per-request wall: threads waiting on IO, memory per thread
3. exec-04 Future, cancellation and interruption: cancel is a request
4. exec-07 CompletableFuture errors, timeouts and fan-out
5. co-02 builders: launch vs async vs coroutineScope waiting for children
6. conc-09 ConcurrentHashMap: bins, per-key atomic compute, compound actions
7. io-01 blocking IO and C10K
8. conc-07 ReentrantLock, Condition and ReadWriteLock
9. rx-05 errors, retries and timeouts as marbles
10. gen-06 use-site variance and type projections
11. perf-02 inlining budget and intrinsics
12. jmm-05 double-checked locking and the holder idiom
13. co-10 shared state: Mutex vs confinement, testing with virtual time
14. conc-11 don't share: immutability, confinement, ThreadLocal
15. mem-06 reading a GC log and sizing the heap in a container
16. perf-05 JDK Flight Recorder: events, recording, reading it

Tier 2
17. rx-04 zip, merge, concat, combineLatest
18. rx-08 hot vs cold, Sinks
19. io-04 Netty codecs, flow control and leaks
20. io-06 Quarkus IO threads, workers and virtual threads
21. vt-03 one virtual thread per task, limits with semaphores
22. exec-01 why pools, and shutdown
23. exec-09 pools in production
24. co-11 coroutines meet Java futures and Reactor
25. cls-05 Byte Buddy and framework proxies
26. gen-02 bounds and constraints
27. gen-10 recursive bounds
28. pat-02 Factory Method and Abstract Factory
29. pat-04 Adapter and Facade
30. pat-10 Visitor and friends
31. dop-02 sealed types
32. boot-01 why the JVM starts slowly

Tier 3
33. conc-01, conc-13, jmm-06, vt-06, gen-09, gen-11, pat-01, pat-03, dop-01, dop-04, kt-05, kt-06, cls-06, perf-07,
    and the capstone lessons cap1-02, cap1-03, cap2-02, cap2-03, cap3-02, cap3-03, cap4-02, cap4-03
