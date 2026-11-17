import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

CHEAT = r"""## The theatre, part by part

The track explains the JVM's backstage with one theatre company. Each picture fits one idea, and each one breaks somewhere: the lessons say where.

| JVM idea | Picture it | Lesson |
|---|---|---|
| bootstrap (`null`), platform and app class loaders, parent-first | the props team: the building's store with no name badge, the props department, the show's stage manager, each asking their senior first | 1 |
| lazy loading; linking; `<clinit>` | a prop fetched only when a scene first needs it; checking it, labelling its spot, filling in the cue sheet; the one dress rehearsal | 1 |
| bytecode, operand stack, local slots, constant pool | the prompt book's shorthand, a stagehand's pile of cue cards, numbered hooks, the glossary | 2 |
| `invokedynamic`, `ConstantCallSite`, `MutableCallSite` | an "ask the director" cue whose answer goes in the margin, in ink or in pencil | 3 |
| JDK proxy, handler, target, self-invocation | a stand-in at the stage door, the stand-in's rule, the actor, the actor talking to themselves | 4 |
| subclass proxy (Byte Buddy, CGLIB, ArC) | a full copy of a role's costume, sewn on the spot; `final` is a role nobody may copy | 5 |
| the proxy is the object, or it forwards | the understudy plays the role, or a lookalike at the door passes requests to the actor, with empty pockets | 5 |
| ClassFile API: parse, build, verify, transform | the theatre's own printing press: read a page into cards, print a new page, a proofreader who checks grammar but never the plot, copy a page keeping, dropping or replacing each line | 6 |
| agent, transformer, retransformation, JEP 451 | a stage manager who slips a note into the prompt book before rehearsal, or pastes a correction over a page mid-run, past a security desk that logs latecomers | 7 |

## Class loading in one table

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
| `Cannot subclass primitive, array or final types` | Byte Buddy was asked to extend a final class, often a Kotlin class without `open` |
| `WARNING: A Java agent has been loaded dynamically` | an agent attached after start-up (JEP 451, JDK 21+) |

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
| top-level `fun f()` in `Lighting.kt` | `static f()` on `LightingKt` |
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
| Picture it | a stand-in at the stage door | a copy of the costume | a note written into the prompt book |
| needs | an interface | a non-final class, non-final methods | an agent (startup or attach) |
| `this.method()` inside the class | not seen | seen only if the proxy is the object | seen |
| final classes/methods | n/a | can't | fine |
| cost per call | a few ns | about 1 ns | the copied code itself |

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
List<VerifyError> errs = ClassFile.of().verify(b);              // check type safety, not correctness
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
| `sun.misc.Unsafe` memory-access warning (JEP 498) | JDK 24 |
"""

T = {
 "id": "cls",
 "intro": "This track goes backstage in the JVM, with a theatre company as the guide. By the end, you can say which class loader defined a class and exactly when its static initializer runs, the way a props team fetches each prop only when a scene needs it. You can read `javap` output for Java and Kotlin, the JVM's prompt book, including the `invokedynamic` cues behind lambdas, string concatenation and records. You can write a JDK dynamic proxy, a stand-in at the stage door, that gets `equals`, exceptions and default methods right. You can build subclass proxies with Byte Buddy, and predict whether Spring, Quarkus ArC or Hibernate will intercept a call, self-calls and Kotlin's final members included. Then you'll read and print class files with the ClassFile API, and change a loaded class under live objects with an agent. Proxies get the most room, in lessons 4 and 5, because they sit under every annotation a framework honours.\n\nYou need to read basic Java and Kotlin, and nothing about the JVM's insides. The *Decorator and Proxy* lesson of the patterns track is a useful warm-up for lesson 4. Install JDK 25. The labs compile with `release 21`, so they run on JDK 21 or later. The ClassFile API is final only from JDK 24, so lesson 6 keeps that code in single-file programs under `labs/bytecode/preview/`, which you run with `java File.java` on JDK 24 or later.\n\nThe labs live in `labs/bytecode`, one package per lesson (`workbench.bytecode.l01` to `l07`). Lessons 1, 3, 4 and 6 are in Java, and lessons 2, 5 and 7 in Kotlin. Every sample and demo comes in both languages. The tests read the JVM's own view of your code: class identity and initialization, the members `javap` would list, call counts through proxies, and a class-file reader checked against ASM. Lesson 7's tests attach an agent to the test JVM, which the build allows with `-XX:+EnableDynamicAgentLoading`. From `labs/`, run `./gradlew :bytecode:test --tests 'workbench.bytecode.lNN.*'` until it passes. What the frameworks do (Spring, Quarkus, Hibernate) comes from their documentation; the track shows both proxy models with Byte Buddy instead of running the frameworks.",
 "cheatsheet": CHEAT,
 "recap": [
  "A class is (binary name, defining loader). Loaders ask their parent first, and the same bytes defined by two loaders are two classes with separate statics.",
  "Loading, linking and initialization are separate and lazy. `<clinit>` runs once, in source order, under a lock: a throw poisons the class (`NoClassDefFoundError` from then on), and two initializers that need each other can deadlock.",
  "javap shows the JVM's shape: a typed operand stack, a constant pool referenced by number, descriptors like `(JI)J`, and Kotlin lowered to getters, `Companion`, `INSTANCE`, `$default` and `final` members.",
  "`invokedynamic` links a call site once, through a bootstrap method. Lambdas become hidden `$$Lambda` classes, and the call site type shows what they capture.",
  "A JDK proxy is a generated `final $ProxyN` that boxes the arguments and calls one handler. Answer `Object` methods by identity, run defaults with `invokeDefault`, unwrap `InvocationTargetException`, and never retry a default method as a whole.",
  "Subclass proxies need non-final classes and methods. Whether self-calls are intercepted depends on whether the proxy is the object (ArC, `@SuperCall`) or forwards to a target (Spring AOP).",
  "The ClassFile API (final in JDK 24) parses class files into lazy models, builds them from lambdas, verifies their types (not their results), and transforms them element by element. The JDK builds its own proxies and lambdas with it.",
  "Agents get an `Instrumentation`: transformers see classes as they load, and retransformation swaps method bodies in place for every caller, never the class's shape. Loading one into a running JVM warns since JDK 21."
 ],
 "quiz": [
  {
   "q": "`static final Integer CURTAIN_MINUTES = 5;` sits in class `ShowConfig`, which also has a `static {}` block that reads a settings file. A test only reads `ShowConfig.CURTAIN_MINUTES`. Does the file get read?",
   "options": [
    "No: it's `static final`, so javac copied the value",
    "Yes: `Integer` isn't a constant variable, so the read initializes `ShowConfig` and runs its static block",
    "Only if the JIT compiled the test",
    "Only the first time the test runs on a machine, because the value is cached on disk"
   ],
   "answer": 1,
   "why": "Only primitives and `String` with constant initializers are constant variables. The boxed `Integer` needs `Integer.valueOf` at run time, so reading it is an ordinary static read that triggers initialization. Make it `static final int` (or Kotlin `const val`), and the read no longer touches the class.",
   "from": "cls-01"
  },
  {
   "q": "A theatre app reloads its scene plugins without a restart, through a new class loader each time. After a reload, the log says `class theatre.Cue cannot be cast to class theatre.Cue`, naming two different loaders. What's the most likely cause?",
   "options": [
    "Two versions of the `Cue` source file",
    "An object created through the previous loader survived the reload, for example in a static cache owned by a loader that outlives it, and met code from the new loader",
    "The JIT inlined an old version of `Cue`",
    "`Cue` is missing `equals`"
   ],
   "answer": 1,
   "why": "Each reload defines `Cue` again in a new loader, so the new `Cue` is a different class from the old one. A reference kept somewhere that outlives the reload still points to an old `Cue`. The same reference also keeps the old loader, and all its classes, in memory.",
   "from": "cls-01"
  },
  {
   "q": "Java code must call a Kotlin `object Lighting { fun fadeSeconds(steps: Long, stepMillis: Int = 32): Long }`. Which Java call compiles with no change to the Kotlin side?",
   "options": [
    "`Lighting.fadeSeconds(12_500)`",
    "`Lighting.INSTANCE.fadeSeconds(12_500, 32)`",
    "`Lighting.fadeSeconds(12_500, 32)`",
    "`Lighting.Companion.fadeSeconds(12_500)`"
   ],
   "answer": 1,
   "why": "An `object` is a class with a `static final INSTANCE`, and its functions are instance methods unless marked `@JvmStatic`. Default values exist only in a synthetic `fadeSeconds$default` method, so Java passes every argument unless the function has `@JvmOverloads`. An `object` has no `Companion`.",
   "from": "cls-02"
  },
  {
   "q": "`javap -c` on a class `Rehearsal` shows `invokedynamic #0:accept:(Ltheatre/Rehearsal;J)Ljava/util/function/Consumer;` inside the method `runAct`. What does each call to `runAct` allocate for that line?",
   "options": [
    "Nothing: lambdas are always shared",
    "One `Consumer` object, because the lambda captures `this` and a `long`",
    "One object per cue the lambda later receives",
    "A new hidden class per call"
   ],
   "answer": 1,
   "why": "The call site type lists the captured values: the `Rehearsal` (`this`) and a `long`. A capturing lambda allocates one object each time its expression is evaluated, so here once per `runAct` call. The hidden class is built once per call site, not per call.",
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
   "why": "`ArrayList.remove(Object)` uses `equals`. A forwarding handler sends it to the target, which doesn't consider the proxy equal to itself. Answer `equals` and `hashCode` by the proxy's identity in the handler.",
   "from": "cls-04"
  },
  {
   "q": "Your retry proxy for `SeatDesk` retries on `DeskUnavailableException`. `holdAndConfirm` is a default method that calls `hold` and then `confirm`. So that a failed confirmation never holds a second seat, how should the handler treat it?",
   "options": [
    "Retry `holdAndConfirm` as a whole, like any other method",
    "Run it with `InvocationHandler.invokeDefault`, so its inner calls come back through the handler and each one is retried on its own",
    "Forward it to the target with `method.invoke`",
    "Skip it: default methods can't be proxied"
   ],
   "answer": 1,
   "why": "With `invokeDefault`, the body runs with `this` as the proxy, so `confirm` is retried as a confirmation, and the `hold` that already worked isn't sent again. Retrying the whole method repeats the hold, and forwarding to the target hides the inner calls from the retry logic.",
   "from": "cls-04"
  },
  {
   "q": "You move the box office app from Spring Boot to Quarkus. `bookAll()` calls `this.book(seat)`, and `book` is `@Transactional`. What changes?",
   "options": [
    "Nothing: both frameworks use proxies the same way",
    "Under Spring, the inner calls had no transaction of their own (the proxy forwards). Under ArC they're intercepted, so each `book` call now gets the transactional interceptor",
    "Quarkus refuses to build the bean",
    "Under Quarkus, the outer call loses its transaction"
   ],
   "answer": 1,
   "why": "Spring's proxy forwards to a separate target, so `this.book()` bypasses it. Quarkus ArC's intercepted subclass is the bean itself, and the Quarkus documentation says self-interception works. Transaction boundaries, and with them locking and saving, can change without a single edited line.",
   "from": "cls-05"
  },
  {
   "q": "Which tool fits each job? You need to (a) time every method of six seat-desk interfaces you own, (b) add a lazily loaded proxy for a database entity class, and (c) count calls to a method of a final class from a library, including its self-calls, without editing it.",
   "options": [
    "(a) JDK proxy, (b) Byte Buddy subclass, (c) agent with Advice",
    "(a) agent, (b) JDK proxy, (c) Spring AOP",
    "(a) Byte Buddy subclass, (b) agent, (c) JDK proxy",
    "All three: a JDK proxy"
   ],
   "answer": 0,
   "why": "You own interfaces, so one JDK proxy handler covers all six. An entity is a class, so a lazy proxy must be a generated subclass, which is what Hibernate builds with Byte Buddy. A final class with self-calls rules out every proxy; an agent's Advice edits the method itself.",
   "from": "cls-05"
  },
  {
   "q": "A hand-written constant-pool reader works on most classes, but fails on one with `unknown constant pool tag 72` near the end. What's the most likely bug?",
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
   "q": "An agent attached to a running program adds a field to `SoundBoard` while retransforming it, so it can count calls. What happens, and what's the fix?",
   "options": [
    "It works for objects created after the attach",
    "`retransformClasses` fails and nothing changes: retransformation can't add fields. Keep the counter in a separate public class that the copied advice calls",
    "The JVM runs `SoundBoard`'s static initializer again",
    "It works, but prints the JEP 451 warning"
   ],
   "answer": 1,
   "why": "Retransformation may change method bodies, the constant pool and attributes, never the class's fields, methods, signatures, modifiers or superclass. Byte Buddy's `disableClassFormatChanges()` plus `Advice` keeps to that rule. The JEP 451 warning is about attaching late, not about what the transformation does.",
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
