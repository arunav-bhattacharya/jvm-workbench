# Track: cls, "Class loading, bytecode and dynamic proxies" (lab: labs/bytecode, package workbench.bytecode.lNN)

Research notes: "research_notes/Advanced JVM runtime topics/classloading_bytecode_proxies.md". The learner asked specially for dynamic
proxies: cls-04 and cls-05 get the most care. pat-05 (Decorator and Proxy) already showed a basic JDK
proxy and the self-invocation pitfall; go deeper here and link back to it. The lab module has Byte
Buddy and byte-buddy-agent (ByteBuddyAgent.install() works in tests; the test JVM already allows
dynamic agent loading). The ClassFile API is final only in JDK 24, so its code lives in single-file
JDK 25 demos under labs/bytecode/preview/ (run with java File.java), not in Gradle.

Lessons:
- cls-01 Class loading: bootstrap/platform/app loaders, parent delegation, loading, linking,
  initialization and when it happens, class-init deadlocks, ClassNotFoundException vs NoClassDefFoundError.
  Lab: an initialization-order puzzle and a loader that loads the same class twice (two Class objects).
- cls-02 Reading bytecode: javap -c -p -v, operand stack, constant pool, descriptors; what Kotlin
  compiles to (properties, companion objects, default args, data classes). Use real javap output.
- cls-03 invokedynamic: bootstrap methods, LambdaMetafactory, indy string concatenation, records'
  ObjectMethods. Lab: build a lambda by hand with LambdaMetafactory (or MethodHandles) and test it.
- cls-04 Dynamic proxies with java.lang.reflect.Proxy: InvocationHandler, generated proxy classes,
  interfaces only, Object methods, default methods via InvocationHandler.invokeDefault (JDK 16),
  caching, cost. Lab: a retrying and timing proxy for a CardIssuerClient interface (tests check retry
  counts, default-method forwarding, equals/hashCode behaviour).
- cls-05 Generated proxies: Byte Buddy subclass proxies and Advice, cglib's status, Spring AOP JDK vs
  CGLIB proxies, Kotlin final classes and all-open, Quarkus ArC build-time interceptors and
  self-invocation, Hibernate lazy proxies. Lab: a Byte Buddy interceptor that times methods of a class.
- cls-06 Generating and transforming classes with the ClassFile API (JDK 24+): models, builders,
  transforms. Gradle lab uses Byte Buddy or ASM-free reflection checks; the ClassFile API code is a
  JDK 25 single-file demo.
- cls-07 Java agents and instrumentation: premain/agentmain, ClassFileTransformer, JEP 451 dynamic
  loading warning, Byte Buddy AgentBuilder. Lab: install an agent at runtime with ByteBuddyAgent and
  count calls to a method.
