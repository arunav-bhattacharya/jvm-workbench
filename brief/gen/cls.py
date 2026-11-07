import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

CHEAT = r"""## Class loading in one table

| Event | Initializes the class? |
|---|---|
| `new X()`, a static method call, a non-constant static field read or write | yes |
| `Class.forName("X")`, a reflective static field read, initializing a subclass | yes |
| reading a `static final` primitive or `String` with a constant value (`const val` in Kotlin) | no: javac copied the value |
| `X.class`, `new X[3]`, `Class.forName("X", false, loader)` | no |
| `Child.field` where `field` is declared in `Parent` | only `Parent` |

A class is (binary name, defining loader). Built-in loaders: bootstrap (`null`), platform, app; parent-first. `<clinit>` runs once, in source order, under a lock.

## Error decoder

| You see | It means |
|---|---|
| `ClassNotFoundException` | an explicit lookup by name (`Class.forName`, `loadClass`) found nothing |
| `NoClassDefFoundError: Could not initialize class X` | X's static initializer threw earlier; look for the first `ExceptionInInitializerError` |
| `NoClassDefFoundError` caused by `ClassNotFoundException` | a class present at compile time is missing at run time |
| `X cannot be cast to class X (... loader 'a' ...; ... loader 'b')` | two loaders defined X: isolation, not a missing jar |
| `UnsupportedClassVersionError ... class file version 69.0` | compiled for Java 25 (69 - 44); the runtime is older |
| `VerifyError: Bad type on operand stack` | generated or edited bytecode is not type-safe |
| two threads `RUNNABLE` "waiting on the Class initialization monitor" | class-initialization deadlock; the deadlock detector won't report it |
| `UndeclaredThrowableException` from a proxy | the handler threw a checked exception the interface method doesn't declare |

## Reading bytecode

`javap -c -p` (code, private members), `-v` (constant pool, `stack=`/`locals=`, `major version`).

| Descriptor | Type |
|---|---|
| `I J Z B C S F D` | int, **long**, **boolean**, byte, char, short, float, double |
| `Lpkg/Name;` | reference type |
| `[J` | `long[]` |
| `(Ljava/lang/String;J)V` | `void m(String, long)` |

`long` and `double` take two local slots, two stack slots and two constant-pool indexes.

| Kotlin | What javap shows |
|---|---|
| `val x` / `var x` | private field + `getX()` (/ `setX()`); `private set` gives no setter |
| `companion object { val X }` | private static field on the class + `Companion.getX()` |
| `const val X` / `@JvmField val X` | `public static final` field (`const` is a real constant) |
| `@JvmStatic fun f()` in a companion | a static `f()` on the class too |
| `object O` | `public static final O INSTANCE` |
| top-level `fun f()` in `Fees.kt` | `static f()` on `FeesKt` |
| default arguments | a synthetic `f$default(..., int mask, Object)`; Java needs `@JvmOverloads` |
| no `open` | `final` class and members |

## invokedynamic

| Source | Bootstrap method |
|---|---|
| lambda, method reference (Java; Kotlin lambdas since 2.0) | `LambdaMetafactory.metafactory` |
| `"a" + b`, Kotlin templates (JVM target 9+) | `StringConcatFactory.makeConcatWithConstants`, recipe with `\u0001` |
| record `toString`/`equals`/`hashCode` | `ObjectMethods.bootstrap` |
| pattern `switch` | `SwitchBootstraps.typeSwitch` (+ condy for enum labels) |

A lambda's call site type lists what it captures: `()Supplier` captures nothing (one shared object), `(LFoo;J)Consumer` captures `this` and a long (a new object per evaluation).

## Three ways to intercept a call

| | JDK proxy | subclass proxy (Byte Buddy, CGLIB, ArC) | agent + Advice |
|---|---|---|---|
| needs | an interface | a non-final class, non-final methods | an agent (startup or attach) |
| `this.method()` inside the class | not seen | seen only if the proxy is the object | seen |
| final classes/methods | n/a | can't | fine |
| cost per call | a few ns | about 1 ns | inlined code |

(Per-call costs are from one indicative JMH run on JDK 25.)

JDK proxy handler, in this order: `Object` methods by identity, defaults via `InvocationHandler.invokeDefault` (JDK 16), the decorated call, `catch (InvocationTargetException e) { throw e.getCause(); }`. Never retry a default method as a whole.

## Frameworks

| | Model | Self-calls intercepted? | Notes |
|---|---|---|---|
| Spring AOP | proxy forwards to a target (JDK proxy or CGLIB) | no | Boot defaults to CGLIB (`spring.aop.proxy-target-class`); final/private methods not advised; Kotlin needs `kotlin-spring` |
| Quarkus ArC | build-time `Foo_Subclass`; `Foo_ClientProxy` for normal scopes | yes (documented, non-standard) | `transform-unproxyable-classes=true` by default; Kotlin guide still uses all-open |
| Hibernate | Byte Buddy lazy proxy subclass | n/a | non-final entity, non-private no-arg constructor, proxy-aware `equals`; `kotlin-jpa` |

## ClassFile API (final in JDK 24, JEP 484)

```java
ClassModel cm = ClassFile.of().parse(bytes);                    // read
byte[] b = ClassFile.of().build(ClassDesc.of("Gen"), clb -> ...); // write
List<VerifyError> errs = ClassFile.of().verify(b);              // check type safety
byte[] t = ClassFile.of().transformClass(cm, ClassTransform.dropping(...)); // pass, drop or replace elements
```

## Agents

| Start | Entry point |
|---|---|
| `-javaagent:a.jar=args` (repeatable, in order) | `premain(String, Instrumentation)` before `main` |
| `Launcher-Agent-Class` in an executable jar | `agentmain` before `main` |
| attach to a running JVM (incl. `ByteBuddyAgent.install()`) | `agentmain`; warns since JDK 21 (JEP 451) |

Retransformation changes method bodies only (no new fields or methods, signatures, modifiers or superclass), keeps statics, reruns no initializer; running frames finish on old code. `-XX:+EnableDynamicAgentLoading` hides the warning, `-XX:-` blocks loading.

## Versions

| What | Since |
|---|---|
| `invokedynamic` / lambdas via `LambdaMetafactory` | Java 7 / 8 |
| indy string concatenation (JEP 280) | JDK 9 |
| hidden classes (`Lookup.defineHiddenClass`) | JDK 15 |
| `InvocationHandler.invokeDefault`, `ObjectMethods` | JDK 16 |
| JEP 451 dynamic-agent warning | JDK 21 |
| ClassFile API preview / final | JDK 22, 23 / 24 |
| JDK proxies / lambdas generated with the ClassFile API | JDK 23 / 24 |
"""

T = {
 "id": "cls",
 "intro": "By the end of this track you can say which loader defined a class and exactly when its static initializer runs, and read `javap` output for Java and Kotlin, including the `invokedynamic` call sites behind lambdas, string concatenation and records. You can write a JDK dynamic proxy that gets `equals`, exceptions and default methods right, build subclass proxies with Byte Buddy, and predict whether Spring, Quarkus ArC or Hibernate will intercept a given call, self-calls and Kotlin's final members included. You'll also read and generate class files with the ClassFile API, and change a loaded class under live objects with an agent. Proxies get the most room, in lessons 4 and 5, because they sit under every annotation your framework honours.\n\nYou need Java and Kotlin, and nothing about the JVM's internals. The *Decorator and Proxy* lesson of the patterns track is a useful warm-up for lesson 4. Install JDK 25. The labs compile with `release 21`, so they run on JDK 21 or later. The ClassFile API is final only from JDK 24, so lesson 6 keeps that code in single-file programs under `labs/bytecode/preview/` that you run with `java File.java` on JDK 24 or later.\n\nThe labs live in `labs/bytecode`, one package per lesson (`workbench.bytecode.l01` to `l07`). Lessons 1, 3, 4 and 6 are in Java, and lessons 2, 5 and 7 in Kotlin. Every sample and demo comes in both languages. The tests read the JVM's view of your code directly: class identity and initialization, the members `javap` would list, call counts through proxies, and a class-file reader checked against ASM. Lesson 7's tests attach an agent to the test JVM, which the build allows with `-XX:+EnableDynamicAgentLoading`. Framework behaviour (Spring, Quarkus, Hibernate) comes from their documentation; the track simulates both proxy models with Byte Buddy rather than running the frameworks.",
 "cheatsheet": CHEAT,
 "recap": [
  "A class is (binary name, defining loader). Loaders delegate parent-first; the same bytes defined by two loaders are two classes with separate statics.",
  "Loading, linking and initialization are separate and lazy. `<clinit>` runs once, in source order, under a lock: a throw poisons the class (`NoClassDefFoundError` forever), and two initializers that need each other can deadlock.",
  "javap shows the JVM's shape: a typed operand stack, a constant pool referenced by index, descriptors like `(JI)J`, and Kotlin lowered to getters, `Companion`, `INSTANCE`, `$default` and `final` members.",
  "`invokedynamic` links a call site once through a bootstrap method. Lambdas become hidden `$$Lambda` classes; the call site type shows what they capture.",
  "A JDK proxy is a generated `final $ProxyN` that boxes arguments and calls one handler. Answer `Object` methods by identity, run defaults with `invokeDefault`, unwrap `InvocationTargetException`, and never retry a default method as a whole.",
  "Subclass proxies need non-final classes and methods. Whether self-calls are intercepted depends on whether the proxy is the object (ArC, `@SuperCall`) or forwards to a target (Spring AOP).",
  "The ClassFile API (final in JDK 24) parses class files into lazy models, builds them from lambdas, verifies them, and transforms them as a flatMap over elements. The JDK builds its own proxies and lambdas with it.",
  "Agents get an `Instrumentation`: transformers see classes as they load, and retransformation swaps method bodies in place, never the class's shape. Dynamic loading warns since JDK 21."
 ],
 "quiz": [
  {
   "q": "`static final Integer TIMEOUT_MS = 120;` sits in class `IssuerConfig`, which also has a `static {}` block that reads a file. A test only reads `IssuerConfig.TIMEOUT_MS`. Does the file get read?",
   "options": [
    "No: it's `static final`, so javac inlined it",
    "Yes: `Integer` isn't a constant variable, so the read initializes `IssuerConfig` and runs its static block",
    "Only if the JIT compiled the test",
    "Only the first time the test runs in a JVM, and the value is cached on disk"
   ],
   "answer": 1,
   "why": "Only primitives and `String` with constant initializers are constant variables. The boxed `Integer` needs `Integer.valueOf` at run time, so reading it is an ordinary static read that triggers initialization. Make it `static final int` (or Kotlin `const val`) and the read no longer touches the class.",
   "from": "cls-01"
  },
  {
   "q": "A Quarkus dev-mode reload logs `class com.acme.Money cannot be cast to class com.acme.Money`, naming two different loaders. What's the most likely cause?",
   "options": [
    "Two versions of the Money source file",
    "An object created by the previous Runtime ClassLoader survived the reload, for example in a static cache owned by a persistent loader, and met code from the new loader",
    "The JIT inlined an old version of Money",
    "Money is missing `equals`"
   ],
   "answer": 1,
   "why": "Dev mode recreates the Runtime ClassLoader on reload, so the new `Money` is a different class from the old one. A reference kept somewhere that outlives the reload still points to an old `Money`. The same pinning keeps the old loader and all its classes in memory.",
   "from": "cls-01"
  },
  {
   "q": "Java code must call `KotlinFees.feeFor(amountMinor)` on a Kotlin `object KotlinFees { fun feeFor(amountMinor: Long, currency: String = \"EUR\"): Long }`. Which Java call compiles with no changes to the Kotlin side?",
   "options": [
    "`KotlinFees.feeFor(1_250)`",
    "`KotlinFees.INSTANCE.feeFor(1_250, \"EUR\")`",
    "`KotlinFees.feeFor(1_250, \"EUR\")`",
    "`KotlinFees.Companion.feeFor(1_250)`"
   ],
   "answer": 1,
   "why": "An `object` is a class with a `static final INSTANCE`, and its functions are instance methods unless marked `@JvmStatic`. Defaults exist only in a synthetic `feeFor$default` method, so Java passes every argument unless the function has `@JvmOverloads`. There's no `Companion` on an `object`.",
   "from": "cls-02"
  },
  {
   "q": "`javap -c` on a Kafka listener shows `invokedynamic #0:accept:(Lcom/acme/LedgerListener;J)Ljava/util/function/Consumer;` inside `onBatch`. What does each call to `onBatch` cost in allocation for that line?",
   "options": [
    "Nothing: lambdas are always shared",
    "One `Consumer` object, because the lambda captures `this` and a `long`",
    "One object per element of the batch",
    "A new hidden class per call"
   ],
   "answer": 1,
   "why": "The call site type lists the captured values: the listener (`this`) and a `long`. Capturing lambdas allocate one object each time the expression is evaluated, so here once per `onBatch` call. The class is spun once per call site, and per-element allocation would need the lambda created inside the loop.",
   "from": "cls-03"
  },
  {
   "q": "Which handler bug makes `listeners.remove(proxy)` on an `ArrayList` return `false` for a JDK proxy that was just added?",
   "options": [
    "Not unwrapping `InvocationTargetException`",
    "Forwarding `equals` to the target, so `proxy.equals(proxy)` asks `target.equals(proxy)`",
    "Using `invokeDefault` for default methods",
    "Creating the proxy with the wrong class loader"
   ],
   "answer": 1,
   "why": "`ArrayList.remove(Object)` uses `equals`. A forwarding handler sends it to the target, which doesn't consider the proxy equal to itself. Answer `equals` and `hashCode` by proxy identity in the handler.",
   "from": "cls-04"
  },
  {
   "q": "Your retry proxy for `CardIssuerClient` retries on `IssuerUnavailableException`. `authorizeAndCapture` is a default method calling `authorize` then `capture`. To make a failed capture never cause a second authorization, how should the handler treat it?",
   "options": [
    "Retry `authorizeAndCapture` as a whole, like any other method",
    "Run it with `InvocationHandler.invokeDefault`, so its inner calls come back through the handler and each is retried on its own",
    "Forward it to the target with `method.invoke`",
    "Skip it: default methods can't be proxied"
   ],
   "answer": 1,
   "why": "With `invokeDefault` the body runs with `this` = the proxy, so `capture` is retried as a capture and the successful `authorize` isn't repeated. Retrying the whole method repeats the authorization, and forwarding to the target hides the inner calls from the retry logic.",
   "from": "cls-04"
  },
  {
   "q": "You move a ledger service from Spring Boot to Quarkus. `postBatch()` calls `this.postEntry()`, which is `@Transactional`. What changes?",
   "options": [
    "Nothing: both frameworks use proxies the same way",
    "Under Spring the inner call had no transaction of its own (the proxy forwards); under ArC it's intercepted, so each `postEntry` now gets the transactional interceptor",
    "Quarkus refuses to build the bean",
    "Under Quarkus the outer call loses its transaction"
   ],
   "answer": 1,
   "why": "Spring's proxy forwards to a separate target, so `this.postEntry()` bypasses it. Quarkus ArC's intercepted subclass is the bean, and the Quarkus docs say self-interception works. Transaction boundaries, and so locking and commit behaviour, can change with no code change.",
   "from": "cls-05"
  },
  {
   "q": "Which tool fits each job? You need to (a) time every method of six issuer client interfaces you own, (b) add a lazily loaded entity proxy, and (c) count calls to a method of a final third-party class, including its self-calls, without editing it.",
   "options": [
    "(a) JDK proxy, (b) Byte Buddy subclass, (c) agent with Advice",
    "(a) agent, (b) JDK proxy, (c) Spring AOP",
    "(a) Byte Buddy subclass, (b) agent, (c) JDK proxy",
    "All three: a JDK proxy"
   ],
   "answer": 0,
   "why": "You own interfaces, so a JDK proxy with one handler covers all six. An entity is a class, so a lazy proxy must be a generated subclass, which is what Hibernate does with Byte Buddy. A final class with self-calls rules out every proxy; an agent's Advice edits the method itself.",
   "from": "cls-05"
  },
  {
   "q": "A hand-written constant-pool reader works on most classes but fails on one with `unknown constant pool tag 72` near the end. What's the most likely bug?",
   "options": [
    "It doesn't handle Kotlin classes",
    "It forgot that `Long` and `Double` entries use two pool indexes, so its count is off and it reads past the pool",
    "The class file is corrupt",
    "It reads big-endian instead of little-endian"
   ],
   "answer": 1,
   "why": "A missed extra index after an 8-byte constant shifts the numbering, so the loop expects one entry more than exists and reads the bytes after the pool as a tag. The symptom shows up far from the cause. Class files are big-endian, which is what `DataInputStream` reads.",
   "from": "cls-06"
  },
  {
   "q": "An agent attached to a running service adds a field to `SettlementJob` while retransforming it, so it can count calls. What happens, and what's the fix?",
   "options": [
    "It works for objects created after the attach",
    "`retransformClasses` fails and nothing changes: retransformation can't add fields. Keep the counter in a separate public class that the inlined advice calls",
    "The JVM restarts `SettlementJob`'s static initializer",
    "It works, but prints the JEP 451 warning"
   ],
   "answer": 1,
   "why": "Retransformation may change method bodies, the constant pool and attributes, never the class's fields, methods, signatures, modifiers or superclass. Byte Buddy's `disableClassFormatChanges()` plus `Advice` keeps to that rule. The JEP 451 warning is about attaching, not about what the transformation does.",
   "from": "cls-07"
  }
 ]
}
# spread the correct answers over the option positions
for q, idx in zip(T["quiz"], [1, 3, 0, 2, 1, 0, 3, 2, 0, 2]):
    right = q["options"].pop(q["answer"])
    q["options"].insert(idx, right)
    q["answer"] = idx
out = ROOT / "content/tracks/cls.json"
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print(out)
