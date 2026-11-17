import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/bytecode/src"
P = "java/workbench/bytecode/l05"
K = "kotlin/workbench/bytecode/l05"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :bytecode:demo -Pmain=workbench.bytecode.l05."

DEMO = {"lang": "java", "title": "TwoModelsDemo.java", "src": read(f"{lab}/demo/{P}/TwoModelsDemo.java"),
        "run": RUN + "TwoModelsDemo", "file": f"{lab}/demo/{P}/TwoModelsDemo.java",
        "alt": {"lang": "kotlin", "title": "TwoModelsDemo.kt", "src": read(f"{lab}/demo/{K}/TwoModelsDemo.kt"),
                "run": RUN + "TwoModelsDemoKt", "file": f"{lab}/demo/{K}/TwoModelsDemo.kt"}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = """<svg viewBox="0 0 680 300" role="img" aria-label="Two proxy models. When the proxy is the object, a call the body makes on this comes back through the interceptor. When the proxy forwards to a separate target, the target's calls on this never reach the proxy.">
<text class="t-s t-m" x="20" y="20">the proxy is the object: Byte Buddy with @SuperCall, Quarkus ArC's Foo_Subclass</text>
<rect class="box" x="20" y="42" width="80" height="44" rx="8"/>
<text class="t-s" x="60" y="68" text-anchor="middle">caller</text>
<rect class="box-ok" x="140" y="30" width="400" height="68" rx="8"/>
<text class="t-s t-m" x="340" y="46" text-anchor="middle">one object: the understudy plays the role</text>
<rect class="box-a" x="160" y="52" width="150" height="38" rx="8"/>
<text class="t-s" x="235" y="75" text-anchor="middle">interceptor</text>
<rect class="box" x="370" y="52" width="150" height="38" rx="8"/>
<text class="t-s t-code" x="445" y="75" text-anchor="middle">original run()</text>
<line class="ln" x1="100" y1="64" x2="156" y2="64" marker-end="url(#arr)"/>
<line class="ln" x1="310" y1="71" x2="366" y2="71" marker-end="url(#arr)"/>
<path class="ln-a" fill="none" d="M445 98 L445 118 L235 118 L235 94" marker-end="url(#arr)"/>
<text class="t-s t-ok" x="340" y="136" text-anchor="middle">this.check() comes back through the interceptor</text>
<text class="t-s t-m" x="20" y="176">the proxy forwards: Spring AOP (a JDK proxy or a CGLIB subclass)</text>
<rect class="box" x="20" y="196" width="80" height="44" rx="8"/>
<text class="t-s" x="60" y="222" text-anchor="middle">caller</text>
<rect class="box-a" x="140" y="196" width="170" height="44" rx="8"/>
<text class="t-s" x="225" y="222" text-anchor="middle">lookalike at the door</text>
<rect class="box" x="370" y="196" width="170" height="44" rx="8"/>
<text class="t-s" x="455" y="222" text-anchor="middle">target object</text>
<line class="ln" x1="100" y1="218" x2="136" y2="218" marker-end="url(#arr)"/>
<line class="ln" x1="310" y1="218" x2="366" y2="218" marker-end="url(#arr)"/>
<path class="ln-bad" fill="none" d="M500 240 L500 262 L410 262 L410 244" marker-end="url(#arr)"/>
<text class="t-s t-bad" x="455" y="284" text-anchor="middle">this.check() stays inside the target</text>
<text class="t-s t-m" x="225" y="262" text-anchor="middle">never sees it</text>
</svg>"""

OPENING = """The stand-in from the last lesson had an easy job. The actor's role came with a job card, an interface that lists what the role does. Most roles have no card. In code, the person who runs the lighting cues is just a class with methods and no interface. For that role, the costume department can sew a full copy of the costume on the spot, so a stand-in can fill it anyway.

Java tools do the same with a subclass, a class that extends yours and replaces some of its methods. Byte Buddy, a library that writes classes while your program runs, does the sewing. Spring and Quarkus, two popular frameworks (libraries that create your objects and connect them), use generated subclasses to add timing or transactions.

The trap is thinking that "it's a subclass" settles everything. Two subclasses can disagree about a method that calls another method of its own object, and a Kotlin class can refuse the costume outright. In this lesson, we'll sew a subclass by hand, then with Byte Buddy, watch two models disagree, and see which one each framework picks. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_HAND = """class TimedCueRunner extends CueRunner {
    @Override
    public String run(String cue) {
        long t0 = System.nanoTime();
        try {
            return super.run(cue);                    // the original body, on THIS object
        } finally {
            log("run", System.nanoTime() - t0);
        }
    }
    // check() the same way; stage() is final, so there is nothing to override
}"""
K_HAND = """class TimedCueRunner : KCueRunner() {                // needs `open class`
    override fun run(cue: String): String {          // needs `open fun`
        val t0 = System.nanoTime()
        try {
            return super.run(cue)                    // the original body, on THIS object
        } finally {
            log("run", System.nanoTime() - t0)
        }
    }
    // check() the same way; stage() is final, so there is nothing to override
}"""
J_BB = """Class<? extends CueRunner> sub = new ByteBuddy()
        .subclass(CueRunner.class)                            // 1. the class to extend
        .method(isDeclaredBy(CueRunner.class))                // 2. which methods to override
        .intercept(MethodDelegation.withDefaultConfiguration()
                .filter(named("intercept"))
                .to(new InSubclass()))                        // 3. who handles each call
        .make()
        .load(CueRunner.class.getClassLoader())               // 4. define it in a new class loader
        .getLoaded();"""
K_BB = """val sub: Class<out KCueRunner> = ByteBuddy()
    .subclass(KCueRunner::class.java)                         // 1. the class to extend
    .method(isDeclaredBy(KCueRunner::class.java))             // 2. which methods to override
    .intercept(MethodDelegation.withDefaultConfiguration()
        .filter { it.name == "intercept" }
        .to(KInSubclass()))                                   // 3. who handles each call
    .make()
    .load(KCueRunner::class.java.classLoader)                 // 4. define it in a new class loader
    .loaded"""

S0 = """The theatre's lighting desk is run by a class called `CueRunner`. Its method `run(cue)` runs one cue, such as `LX-14`, and first calls `this.check(cue)` to make sure the cue exists. A third method, `stage()`, is `final` and names the stage. There's no interface anywhere, so the stand-in from the last lesson can't help: `Proxy` only implements interfaces.

A subclass can help. A subclass extends a class and may override its methods, that is, replace them with its own versions. Here is a timing stand-in, written by hand:

""" + pair(J_HAND, K_HAND) + """

Each override is a place to add work around the original method, and `super.run(cue)` runs the original body on this same object. That's the costume: every caller sees a `CueRunner`, because the subclass is one, and it can add a step before and after each method of the role.

Writing such a class for every class you own is slow and easy to get wrong. Byte Buddy, a library for writing classes while a program runs, sews the subclass for you. You say which class to extend, which methods to override, and who handles each call:

""" + pair(J_BB, K_BB) + """

The handler, `InSubclass`, is an interceptor: an object whose method runs in place of the original and decides when to call it. Byte Buddy chooses what to pass it by the annotations on its parameters. `@Origin Method` is the method being called. `@SuperCall Callable` is a small object that runs the original body when you call it. The demo's interceptor logs the method's name, then calls the original. Here's what the demo prints about the class it got back:

```text
generated workbench.bytecode.l05.TwoModelsDemo$CueRunner$ByteBuddy$YUk6Nqln
declares  [check, check$accessor$AJXfCzMY, run, run$accessor$AJXfCzMY]
ran LX-14 (checked LX-14), on the main stage
```

The name ends in `$ByteBuddy$` and a suffix that is random on every run. The class declares `run` and `check`, plus an accessor for each: a helper method that calls `super.run(...)` for the interceptor's `Callable`, just as you did by hand. `stage()` isn't there at all, yet it still answered `main stage`.

A subclass can only intercept what it can override, and that one rule sets the limits of every subclass proxy. A `final` class can't be extended at all. A `final` or `private` method can't be overridden, so it runs as written and no interceptor sees it. And every subclass object is built by a constructor, which runs the superclass constructor too.

Kotlin meets the first limit every day, because its classes and their members are `final` unless you write `open`. The demo's last line asks for a costume for a plain Kotlin class:

```text
Kotlin class without open: Cannot subclass primitive, array or final types: class workbench.bytecode.l05.KotlinCueRunner
```

Kotlin locked the door, and Byte Buddy doesn't pick locks. You can write `open` on the class and on each method. Or a compiler plugin can do it for you. The Kotlin all-open plugin "makes classes and their members open at compile time without requiring the `open` keyword". It does that for classes that carry annotations you choose.

**A subclass proxy can only intercept what it can override. Look for `final` first.**

Byte Buddy is the library most Java tools use for this, and the labs use version 1.18.17. You may also meet cglib, an older library for the same job. Its own README says it "is unmaintained and does not work well (or possibly at all?) in newer JDKs, particularly JDK17+", and points to Byte Buddy. Spring still uses cglib, through a copy that the Spring team patches and ships inside Spring, as `org.springframework.cglib`.

So the costume department can sew for any role that isn't locked. The next question is who wears the costume."""

# ---------------------------------------------------------------- section 1
J_FWD = """class ForwardingCueRunner extends CueRunner {
    private final CueRunner target;
    ForwardingCueRunner(CueRunner target) { this.target = target; }

    @Override
    public String run(String cue) {
        log("run");
        return target.run(cue);                       // the body runs on the target
    }
    // check() the same way
}"""
K_FWD = """class ForwardingCueRunner(private val target: KCueRunner) : KCueRunner() {
    override fun run(cue: String): String {
        log("run")
        return target.run(cue)                        // the body runs on the target
    }
    // check() the same way
}"""

S1 = """The costume fits, but it can be worn in two ways. They give opposite answers for `run("LX-14")`, whose body calls `this.check(cue)`.

In the first way, the understudy wears the costume and plays the role. There's no other actor: the generated subclass object is the only `CueRunner`, and the interceptor runs the original body on it through `@SuperCall`. When that body calls `this.check(...)`, `this` is the subclass object. The call goes to its override, and the interceptor runs again. The demo logs both calls:

```text
subclass model:   [intercepted run, intercepted check]
```

In the second way, a lookalike in the costume stands at the stage door and passes each request to the real actor inside. The subclass object is only a front for a separate object, the target. Written by hand, it looks like this:

""" + pair(J_FWD, K_FWD) + """

The demo's `Forwarding` interceptor does the same with `method.invoke(target, args)`. The body runs on the target, where `this` is the target. So `this.check(...)` is an ordinary call inside the target. It's the actor talking to themselves, from the last lesson, and it never comes back out through the door:

```text
ran LX-15 (checked LX-15)
forwarding model: [forwarded run], constructors run: 2
```

Here the costume picture breaks. Putting on a costume doesn't create a second actor, but creating a subclass object does create a second object. Java ran `CueRunner`'s constructor twice: once for the target, and once for the proxy, because `newInstance` builds the subclass the normal way. Two cue runners were built to run one cue. Spring's documentation for its version 3.2 warned about exactly that: "The constructor of your proxied object will be called twice".

The second object also has fields of its own, like a costume with empty pockets. Anything the lookalike can't pass on, such as a `final` method, runs on the lookalike itself, from those empty pockets. The lab tests this with its `BoxOffice` class. A forwarding proxy answers `welcome()` from its own `venue` field, which still says `"unset"`, while the target's says `"the Riverside"`.

So "it's a subclass" doesn't settle the question. Ask where the body runs. If the proxy is the object, self-calls are intercepted, and final methods run on the real fields. If the proxy forwards, self-calls skip it, and final methods run on the proxy's own fields.

**Self-calls are intercepted only when the proxy is the object. Ask where the body runs.**

Frameworks pick one model or the other, and the code you write rarely shows which. The next two sections take Spring and then Quarkus, from their documentation. This track runs neither framework: the Byte Buddy demo stands in for both models."""

# ---------------------------------------------------------------- section 2
S2 = """Spring is a framework that creates your application's objects, which it calls beans, and connects them to each other. Spring AOP, for aspect-oriented programming, is how it adds the same extra work, such as timing or transactions, around many methods without editing each one. Spring calls that extra work **advice**, and a method that gets it is advised.

Spring's reference documentation gives the choice of proxy in one rule: "If the target object to be proxied implements at least one interface, a JDK dynamic proxy is used, and all of the interfaces implemented by the target type are proxied. If the target object does not implement any interfaces, a CGLIB proxy is created which is a runtime-generated subclass of the target type."

Spring Boot, the part of Spring that sets up an application with sensible defaults, changes that default. Its `AopAutoConfiguration` turns on class-based proxies unless you set `spring.aop.proxy-target-class=false`. So in a Boot application, expect CGLIB subclasses even for beans that have interfaces. Spring Framework 7.0 adds `@Proxyable(INTERFACES)` and `@Proxyable(TARGET_CLASS)` to choose for one bean.

Either way, the proxy forwards to a separate target bean: the lookalike at the door. The rules follow from the first section, and the documentation lists them for CGLIB proxies: "`final` classes cannot be proxied", "`final` methods cannot be advised", "`private` methods cannot be advised".

The constructor no longer runs twice. Spring now creates the CGLIB proxy object through Objenesis, a library that makes objects without running any constructor. The price is the empty pockets: a final method that runs on the proxy sees fields that were never set, often `null`.

The best-known advice is `@Transactional`. A database transaction is a group of changes that is saved all together or not at all, and this annotation asks Spring to start one around the method. The documentation spells out what proxy mode, the default, means for it. "Only external method calls coming in through the proxy are intercepted", so self-invocation "does not lead to an actual transaction at runtime". Since Spring 6.0, `@Transactional` also works on `protected` and package-visible methods when the proxy is class-based. Interface-based proxies need public methods declared in the interface.

The documented ways out of self-invocation, best first, are these. Restructure so the call crosses from one bean to another. Inject the bean into itself and call the proxy. Or call `AopContext.currentProxy()`, which the documentation itself calls "highly discouraged". There's also AspectJ mode, where a tool called AspectJ weaves the advice into your class's own bytecode, so there is no proxy at all.

Kotlin adds one requirement. The `kotlin-spring` compiler plugin is "a preconfigured wrapper around the all-open plugin". It opens classes annotated with `@Component`, `@Async`, `@Transactional`, `@Cacheable` and `@SpringBootTest`, and, through `@Component`, also `@Service`, `@Repository`, `@Controller`, `@RestController` and `@Configuration`. Projects made on start.spring.io turn it on by default. Without it, a Kotlin bean is a `final` class that CGLIB can't extend. Write `open class` by hand and forget `open fun`, and you get the quieter failure: methods that are never advised.

**In Spring, advice runs only on calls that come in through the proxy. Keep advised methods open, and call them from another bean.**

Spring sews its costumes while the application starts. Quarkus sews them earlier."""

# ---------------------------------------------------------------- section 3
S3 = """Quarkus is a framework designed to do as much work as it can while your application is built, so that less is left for start-up. Its container, ArC, is the part that creates beans and runs interceptors around their methods. ArC follows CDI, the Jakarta Contexts and Dependency Injection standard, which defines how a container creates objects, wires them together and intercepts their methods. In CDI, an interceptor is a class that a container runs around each method carrying a matching annotation, such as `@Transactional`.

ArC writes its proxy classes during the build, as ordinary class files, so the costume is sewn before the doors open. Its source names them in comments: "Foo_Subclass extends Foo implements Subclass" for a bean with interceptors, and "Foo_ClientProxy extends Foo implements ClientProxy" for a client proxy. Both are subclasses of your class, playing two different roles.

A client proxy is the forwarding model, used for scopes. A scoped bean has one instance per scope, such as one per application (`@ApplicationScoped`) or one per web request (`@RequestScoped`). The Quarkus documentation calls a client proxy "an object that delegates all method invocations to a target bean instance". The real instance is created on the first method call. That's why the documentation says to "never read or write a field of a normal scoped bean" from outside: you'd be reading the lookalike's empty pockets. A `@Singleton` bean has no client proxy.

The intercepted subclass is the other model. The Quarkus CDI reference says: "Quarkus supports what is known as intercepted self-invocation or just self-interception - a scenario where CDI bean invokes its own intercepted method from within another method while triggering any associated interceptors." It calls this a non-standard feature, because the CDI specification doesn't say whether self-interception should work. Given `Foo_Subclass extends Foo`, the natural reading is that the subclass object is the bean itself, the understudy who plays the role, so `this.book(seat)` reaches the intercepting override. That mechanism is an inference from the documentation and the class names; this track didn't trace it in ArC's source. The behaviour itself is documented. A client proxy in front of an intercepted bean forwards to that subclass object, so both kinds can apply at once.

So a class can change behaviour when it moves from Spring to Quarkus, without one edited line. Take a `BoxOffice` whose `bookAll(seats)` calls `this.book(seat)`, with `@Transactional` on `book`. Under Spring, the inner calls got no transaction of their own. Under ArC, each `book` call gets one, and the reverse move loses them.

ArC also works around Kotlin's `final` classes. `quarkus.arc.transform-unproxyable-classes` is `true` by default and lets Quarkus proxy final classes and classes with final methods. The Quarkus Kotlin guide still sets up the all-open plugin for `@Path`, `@ApplicationScoped` and database entity classes. Follow the guide, and check with javap and a test before you assume either one is unnecessary.

Every tool in this lesson adds work the same way, by overriding, so they share one limit. A `final` class from a library you can't recompile stays out of reach, and so does every `final` method inside it."""

ASIDE = {
 "title": "Are database entities proxied the same way?",
 "body": "Yes, with the same rules. Hibernate, a library that maps objects to database tables, can load a related object lazily, through a subclass proxy that it generates with Byte Buddy. Such a proxy \"masquerades as a real entity\" but holds no data until you call one of its methods. So an entity \"must be a non-`final` class, with a non-`private` constructor with no parameters\". Your `equals()` \"must be written to accommodate the possibility that the object passed to the equals() might be a proxy\": a `getClass()` check fails, because the proxy's class is the generated subclass. For Kotlin, the kotlin-jpa plugin opens entities and adds the constructor with no parameters."
}

L = {
 "id": "cls-05",
 "title": "Generated proxies: Byte Buddy, Spring AOP and Quarkus interceptors",
 "minutes": 40,
 "goal": "By the end you can build a subclass proxy with Byte Buddy, tell the two proxy models apart (the proxy is the object, or the proxy forwards to a target), and predict from that whether Spring, Quarkus ArC or Hibernate will intercept a call, including self-calls and Kotlin's final members.",
 "opening": OPENING,
 "warmup": {
  "q": "A box office class has `bookAll(seats)`, which calls `this.book(seat)` for each seat. `book` carries `@Transactional`, an annotation that asks the framework to run each call in a database transaction (a group of changes saved all together or not at all). The same class runs once under Spring Boot and once under Quarkus. Does each inner `book` call get a transaction?",
  "options": [
   "Yes in both: the annotation is on the method",
   "No in Spring, yes in Quarkus",
   "Yes in Spring, no in Quarkus",
   "No in both: a call through `this` never passes a proxy"
  ],
  "answer": 1,
  "why": "Spring's proxy, a JDK proxy or a CGLIB subclass, forwards each call to a separate target object, so `this.book` inside the target never passes the proxy. Quarkus's container, ArC, intercepts through a generated subclass that is the object itself, and its documentation says self-interception works (as a non-standard addition to CDI). The annotation is the same in both; where the real object lives is what differs. The section on the two models shows it with a running program."
 },
 "sections": [
  {
   "h": "Sewing the costume: a subclass that overrides every method it can",
   "body": S0,
   "try": {
    "title": "Generate a subclass, then try a Kotlin class",
    "minutes": 4,
    "steps": [
     "Run `TwoModelsDemo` (or the Kotlin twin) and read the first three lines and the last line.",
     "In `TwoModelsDemo.kt`, open `KotlinCueRunner`: `open class KotlinCueRunner { open fun run(cue: String) = ... }`. Before you run either version again, predict what happens to the last line.",
     "From `labs/`, run `javap -p bytecode/build/classes/kotlin/demo/workbench/bytecode/l05/KCueRunner.class` and find the one method that is still `final`."
    ],
    "code": DEMO,
    "expect": "The generated class name ends in `$ByteBuddy$` plus a random suffix, and it declares `check`, `run` and an `$accessor$` method for each. The last line is `Kotlin class without open: Cannot subclass primitive, array or final types: class workbench.bytecode.l05.KotlinCueRunner`. After adding `open`, that line disappears, because `make()` now succeeds. In javap, `run` and `check` are plain `public`, while `stage()` is `public final`: kotlinc keeps a member final unless you mark it `open`, even inside an open class."
   },
   "refs": [
    {"title": "Byte Buddy README (tutorial examples, Java version support)", "url": "https://github.com/raphw/byte-buddy/blob/master/README.md", "kind": "read"},
    {"title": "All-open compiler plugin (Kotlin docs)", "url": "https://kotlinlang.org/docs/all-open-plugin.html", "kind": "docs"}
   ]
  },
  {
   "h": "Who wears the costume: the proxy is the object, or it forwards to one",
   "body": S1,
   "figure": {"svg": FIG, "caption": "If the proxy is the object, a call on this goes through the interceptor again. If the proxy forwards, the target's own calls never leave the target."},
   "try": {
    "title": "Watch the two models disagree",
    "minutes": 4,
    "steps": [
     "Run `TwoModelsDemo` again and compare the `subclass model` and `forwarding model` lines, and the constructor count.",
     "Predict what the subclass-model log shows if `check` is `final` (in Java, add `final`; in Kotlin, remove `open`). Run it.",
     "Undo that. Then explain in one sentence why no change inside `Forwarding.intercept` could make it see the target's `this.check` call."
    ],
    "code": DEMO,
    "expect": "`subclass model: [intercepted run, intercepted check]` and `forwarding model: [forwarded run], constructors run: 2`. With `check` final, the subclass model logs only `[intercepted run]`, and the class declares only `run` and its accessor: Byte Buddy can't override `check`, so the self-call runs the original directly. The forwarding interceptor only sees calls made on the proxy object, and the target's `this.check` is a call on the target, so nothing the proxy does can see it."
   }
  },
  {
   "h": "Spring AOP: a lookalike at the door, in front of a separate target",
   "body": S2,
   "try": {
    "title": "Read a class the way CGLIB would",
    "minutes": 3,
    "steps": [
     "Open `labs/bytecode/src/main/kotlin/workbench/bytecode/l05/BoxOffice.kt`, the lab's starting point. Compile it with `./gradlew :bytecode:classes` from `labs/`.",
     "Run `javap -p bytecode/build/classes/kotlin/main/workbench/bytecode/l05/BoxOffice.class`.",
     "Mark each member: could a CGLIB subclass advise it? Then say what Spring would do with a `@Transactional` on `price`."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "./gradlew :bytecode:classes\njavap -p bytecode/build/classes/kotlin/main/workbench/bytecode/l05/BoxOffice.class", "run": ""},
    "expect": "`public final class workbench.bytecode.l05.BoxOffice`, and every method `public final`, the getter and setter of `venue` included. Nothing can be advised, and the class itself can't be extended, so Spring couldn't build a CGLIB proxy for it at all. With `kotlin-spring` and a Spring annotation on the class, kotlinc would write the class and its members without `final`. In the lab you add `open` by hand."
   },
   "refs": [
    {"title": "Spring Framework reference: Proxying mechanisms", "url": "https://docs.spring.io/spring-framework/reference/core/aop/proxying.html", "kind": "docs"},
    {"title": "kotlin-spring compiler plugin (Kotlin docs)", "url": "https://kotlinlang.org/docs/kotlin-spring-plugin.html", "kind": "docs"}
   ]
  },
  {
   "h": "Quarkus ArC: costumes sewn at build time, and self-calls intercepted",
   "body": S3,
   "aside": ASIDE,
   "refs": [
    {"title": "Quarkus: Contexts and Dependency Injection reference (ArC)", "url": "https://quarkus.io/guides/cdi-reference", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "A timing subclass proxy in Java and Kotlin",
  "java": {"title": "TimedSubclass.java", "src": "public class SuperCallTimer {\n    @RuntimeType\n    public Object intercept(@Origin Method m, @SuperCall Callable<?> original) throws Exception {\n        long t0 = System.nanoTime();\n        try {\n            return original.call();          // the original body, on this same object\n        } finally {\n            System.out.println(m.getName() + \" took \" + (System.nanoTime() - t0) + \" ns\");\n        }\n    }\n}\n\n// a Java class and its methods are open by default; final methods would be skipped\nBoxOffice timed = new ByteBuddy()\n        .subclass(BoxOffice.class)\n        .method(isPublic().and(isDeclaredBy(BoxOffice.class)))\n        .intercept(MethodDelegation.withDefaultConfiguration()\n                .filter(named(\"intercept\")).to(new SuperCallTimer()))\n        .make().load(BoxOffice.class.getClassLoader()).getLoaded()\n        .getDeclaredConstructor().newInstance();"},
  "kotlin": {"title": "TimedSubclass.kt", "src": "class SuperCallTimer {\n    @RuntimeType\n    fun intercept(@Origin m: Method, @SuperCall original: Callable<*>): Any? {\n        val t0 = System.nanoTime()\n        try {\n            return original.call()           // the original body, on this same object\n        } finally {\n            println(\"${m.name} took ${System.nanoTime() - t0} ns\")\n        }\n    }\n}\n\n// BoxOffice and each method must be `open` (or opened by all-open)\nval timed: BoxOffice = ByteBuddy()\n    .subclass(BoxOffice::class.java)\n    .method(isPublic<MethodDescription>().and(isDeclaredBy(BoxOffice::class.java)))\n    .intercept(MethodDelegation.withDefaultConfiguration()\n        .filter(named(\"intercept\")).to(SuperCallTimer()))\n    .make().load(BoxOffice::class.java.classLoader).loaded\n    .getDeclaredConstructor().newInstance()"},
  "note": "The Byte Buddy calls are the same in both. What changes is what there is to intercept. A Java class and its methods are open unless marked `final`. A Kotlin class and its members are final unless marked `open`, so the same builder quietly skips every Kotlin method you didn't open, and refuses the class outright if the class itself is final. Kotlin also needs the type argument in `isPublic<MethodDescription>()`, because the matcher is generic and nothing else tells the compiler its type. In both, `filter(named(\"intercept\"))` stops Byte Buddy from treating the interceptor's other methods, such as `equals` and `toString`, as candidates, which otherwise fails with \"Cannot resolve ambiguous delegation\"."
 },
 "worked": {
  "title": "A @Transactional Kotlin method that never starts a transaction",
  "steps": [
   {"say": "A Spring Boot service in Kotlin books seats. `SeatRepository` is the bean that saves them to a database. Someone added `open` to the class so Spring could build its proxy, and the application starts fine. Before reading on: does `book` run in a transaction when a web controller, the class that handles a request, calls it?", "code": "@Service\nopen class BookingService(private val seats: SeatRepository) {\n    @Transactional\n    fun book(seat: String) {          // no `open`\n        seats.save(seat)\n    }\n}", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "// the Java equivalent of what kotlinc wrote\n@Service\npublic class BookingService {\n    private final SeatRepository seats;\n    public BookingService(SeatRepository seats) { this.seats = seats; }\n\n    @Transactional\n    public final void book(String seat) {      // final: CGLIB can't override it\n        seats.save(seat);\n    }\n}"},
   {"say": "Check the JVM's view. `javap -p` shows the class without `final`, which is why Spring could build its CGLIB subclass. But `book` is still `public final void book(java.lang.String)`, and the Spring documentation says \"`final` methods cannot be advised\". So the controller calls the proxy, the proxy can't override `book`, and the inherited body runs on the proxy object, with no transaction.", "code": "public class BookingService {\n  private final SeatRepository seats;\n  public BookingService(SeatRepository);\n  public final void book(java.lang.String);     // 1. final: never advised\n}", "lang": "text"},
   {"say": "It's worse than a missing transaction. The body runs on the proxy, not on the target, and Spring builds CGLIB proxies through Objenesis, which skips constructors. On the proxy, `seats` was never set: the lookalike's pockets are empty. The forwarding test in this lesson's lab shows the same effect with Byte Buddy, where a final method reads the proxy's own field instead of the target's. Expect a `NullPointerException` on `seats`, or quietly wrong data.", "code": "", "lang": ""},
   {"say": "Fix it in the build, not one method at a time. The `kotlin-spring` plugin opens classes annotated with `@Service` or `@Transactional`, and their members, so `book` compiles without `final`. Then keep calls to `book` coming from outside the bean, because the proxy still forwards, and a self-call would still skip it.", "code": "// build.gradle.kts\nplugins {\n    kotlin(\"jvm\") version \"2.4.21\"\n    kotlin(\"plugin.spring\") version \"2.4.21\"   // all-open preset for Spring annotations\n}", "lang": "kotlin", "solo": True}
  ]
 },
 "lab": {
  "title": "Time a Kotlin class with Byte Buddy, two ways",
  "minutes": 15,
  "files": [
   "labs/bytecode/src/main/kotlin/workbench/bytecode/l05/BoxOffice.kt",
   "labs/bytecode/src/main/kotlin/workbench/bytecode/l05/TimingProxies.kt"
  ],
  "run": "./gradlew :bytecode:test --tests 'workbench.bytecode.l05.*'",
  "steps": [
   "Run the tests once. All six fail with `NotImplementedError`. Read `BoxOffice`: `price(zone, seats)` adds up the seats and the booking fee by calling two of its own methods, `seatPrice` and `bookingFee`, on `this`.",
   "In `TimingProxies`, write a private `build(type, interceptor)` that does `ByteBuddy().subclass(type).method(isPublic<MethodDescription>().and(isDeclaredBy(type))).intercept(MethodDelegation.withDefaultConfiguration().filter(named(\"intercept\")).to(interceptor)).make().load(type.classLoader).loaded.getDeclaredConstructor().newInstance()`.",
   "Write a `SuperCallInterceptor(clock, sink)` class with `@RuntimeType fun intercept(@Origin method: Method, @SuperCall zuper: Callable<*>): Any?`. Read the clock, call `zuper.call()`, read the clock again and record the call. On an exception, record it with `failed = true` and rethrow it. Use it in `subclassTimed`.",
   "Run the tests. Now they fail with `Cannot subclass primitive, array or final types`. Open `BoxOffice` and its three price methods, but leave `welcome` final. Run again and watch the self-call test pass.",
   "Write a `ForwardingInterceptor(target, clock, sink)` whose `intercept(@Origin method: Method, @AllArguments args: Array<Any?>)` times `method.invoke(target, *args)` and unwraps `InvocationTargetException`. Use it in `forwardingTimed`. Run until all six pass."
  ],
  "hints": [
   "`Cannot resolve ambiguous delegation ... to ... toString() or ...` means Byte Buddy considered other methods of your interceptor. Keep the `filter(named(\"intercept\"))`.",
   "The fake clock moves 1 ms per read. `price` should record `5ms` in the subclass model (its own two reads, plus two for each inner call) and `1ms` in the forwarding model.",
   "Interceptor classes must be public (Kotlin's default), because the generated class lives in a child class loader and calls them from outside your own code."
  ],
  "done_when": "All six tests in `TimingProxiesTest` pass, and `welcome` is still final."
 },
 "drill": {
  "title": "Which model, which result?",
  "minutes": 4,
  "prompt": "Close the page. Write the two Byte Buddy interceptors from memory: one that runs the original body on the same object, and one that forwards to a target. Then answer: in each model, is `this.check()` inside `run()` intercepted, and what does a `final` method see?",
  "answer": {
   "lang": "java",
   "src": "// 1. the proxy IS the object: self-calls intercepted, final methods run on the real fields\npublic class InSubclass {\n    @RuntimeType\n    public Object intercept(@Origin Method m, @SuperCall Callable<?> original) throws Exception {\n        return original.call();\n    }\n}\n\n// 2. the proxy forwards: self-calls skip it, final methods run on the proxy's own fields\npublic class Forwarding {\n    private final Object target;\n    public Forwarding(Object target) { this.target = target; }\n\n    @RuntimeType\n    public Object intercept(@Origin Method m, @AllArguments Object[] args) throws Throwable {\n        try {\n            return m.invoke(target, args);\n        } catch (InvocationTargetException e) {\n            throw e.getCause();\n        }\n    }\n}",
   "alt": {"lang": "kotlin", "src": "// 1. the proxy IS the object: self-calls intercepted, final methods run on the real fields\nclass InSubclass {\n    @RuntimeType\n    fun intercept(@Origin m: Method, @SuperCall original: Callable<*>): Any? = original.call()\n}\n\n// 2. the proxy forwards: self-calls skip it, final methods run on the proxy's own fields\nclass Forwarding(private val target: Any) {\n    @RuntimeType\n    fun intercept(@Origin m: Method, @AllArguments args: Array<Any?>): Any? =\n        try {\n            m.invoke(target, *args)\n        } catch (e: InvocationTargetException) {\n            throw e.cause!!\n        }\n}"}
  }
 },
 "recap": [
  "A subclass proxy (Byte Buddy, Spring's CGLIB, Quarkus ArC, Hibernate) wraps a class with no interface, but only what it can override: no `final` classes, no `final` or `private` methods.",
  "Kotlin classes and members are final by default. Use `open`, or the all-open, `kotlin-spring` or kotlin-jpa plugins, and check the result with `javap -p`.",
  "There are two models. If the proxy is the object (ArC's `_Subclass`, `@SuperCall`), self-calls are intercepted. If it forwards to a target (Spring AOP), self-calls skip it.",
  "On a forwarding proxy, a method it can't override runs on the proxy object itself, with the proxy's own fields, which Objenesis-built proxies never set.",
  "Spring uses a JDK proxy for a bean with interfaces and CGLIB otherwise, but Spring Boot defaults to class-based proxies. Quarkus ArC writes its proxies at build time and documents self-interception.",
  "The limit: every subclass proxy needs a class it can extend. A final class from a library you can't recompile, and its final methods, stay out of reach."
 ],
 "closing": "We started with a role that had no job card, and a costume department that sews a full copy of the costume. Byte Buddy, Spring's CGLIB and Quarkus ArC all sew subclasses, and all stop at `final`. What decides self-calls is who wears the costume: an understudy who is the object, or a lookalike who forwards to it.\n\nNow find a method in your code with an annotation such as `@Transactional` or `@Cacheable`, and check two things. Is it `open`, or opened by a plugin? And is it ever called through `this`?\n\nNext, we'll open the bytes these tools hand to the class loader. What is inside a class file, and how does the JDK's own ClassFile API write one?",
 "quiz": [
  {
   "q": "A Spring Boot application has `class TicketService implements Tickets` with a `@Transactional` method, and no proxy settings. What kind of proxy does Spring Boot put in front of it by default?",
   "options": [
    "A JDK dynamic proxy, because the class implements an interface",
    "A CGLIB subclass of `TicketService`, because Boot sets `proxyTargetClass=true` unless `spring.aop.proxy-target-class=false`",
    "No proxy: `@Transactional` is applied by an agent",
    "A Byte Buddy subclass"
   ],
   "answer": 1,
   "why": "Spring Framework on its own would pick a JDK proxy for a bean with interfaces. Spring Boot's `AopAutoConfiguration` turns on class-based proxies by default. Either kind forwards to a separate target, so the self-invocation rules are the same."
  },
  {
   "q": "Kotlin: `@Service open class Bookings { @Transactional fun book(seat: String) { repo.save(seat) } }`, without the kotlin-spring plugin. A controller calls `bookings.book(\"B12\")`. What happens?",
   "options": [
    "`book` runs in a transaction",
    "Start-up fails: Spring can't proxy the class",
    "`book` is `final`, so the CGLIB proxy can't advise it. The body runs on the proxy object, without a transaction, where `repo` may be null",
    "Spring builds an interface-based proxy instead"
   ],
   "answer": 2,
   "why": "`open class` lets CGLIB extend the class, but each member is still `final` unless marked `open`. A final method is inherited unchanged, so calling it on the proxy runs the body on the proxy object, which Spring created through Objenesis without running a constructor. `kotlin-spring` opens the members as well."
  },
  {
   "q": "In a Quarkus `@ApplicationScoped` bean, `bookAll()` calls `this.book(seat)`, and `book` is `@Transactional`. Which statement matches the Quarkus documentation?",
   "options": [
    "The inner call is intercepted: ArC supports intercepted self-invocation, as a non-standard feature",
    "The inner call skips the interceptor, as in Spring",
    "It depends on `quarkus.arc.transform-unproxyable-classes`",
    "Quarkus rejects self-invocation at build time"
   ],
   "answer": 0,
   "why": "The Quarkus CDI reference says ArC supports self-interception: calling an intercepted method from another method of the same bean still triggers its interceptors. It's non-standard because the CDI specification doesn't define it. `transform-unproxyable-classes` is about final classes and methods, not self-calls."
  },
  {
   "q": "Which change makes an entity class usable for Hibernate's lazy proxies?",
   "options": [
    "Mark the entity `final` so Hibernate can inline it",
    "Keep it non-final and give it a non-`private` constructor with no parameters",
    "Declare collection fields as `ArrayList` instead of `List`",
    "Make `equals` compare `getClass()` of both objects"
   ],
   "answer": 1,
   "why": "Hibernate generates a subclass of the entity, so the class must not be final and needs a non-private constructor with no parameters. Collection fields must use interface types, because Hibernate puts its own collection classes there. A `getClass()` comparison in `equals` fails against a proxy, whose class is the generated subclass."
  },
  {
   "q": "From *Dynamic proxies with java.lang.reflect.Proxy*: you call `Proxy.newProxyInstance(loader, new Class<?>[]{BoxOffice.class}, h)`, where `BoxOffice` is a class with no interface. What happens?",
   "options": [
    "A subclass proxy is generated instead",
    "`IllegalArgumentException: ... BoxOffice is not an interface`",
    "It works, but only public methods reach the handler",
    "`UndeclaredThrowableException`"
   ],
   "answer": 1,
   "why": "A JDK proxy class implements interfaces and extends `java.lang.reflect.Proxy`, so it can't extend your class. To intercept a class, a library must generate a subclass, which is what Byte Buddy, Spring's CGLIB, ArC and Hibernate do.",
   "from": "cls-04"
  }
 ],
 "flashcards": [
  {"front": "What can a subclass proxy never intercept?", "back": "Anything it can't override: a `final` class (no proxy at all), `final` methods and `private` methods. Those run as written."},
  {"front": "Why does a plain Kotlin class fail with Byte Buddy, CGLIB or Hibernate?", "back": "Kotlin classes and members are `final` by default. Byte Buddy says `Cannot subclass primitive, array or final types`."},
  {"front": "When the proxy is the object (`@SuperCall`, ArC's `_Subclass`), is a self-call `this.check()` intercepted?", "back": "Yes. `this` is the generated subclass, so the call goes to its overriding method, and the interceptor runs."},
  {"front": "On a forwarding proxy (Spring style), where does a `final` method run?", "back": "On the proxy object itself, with the proxy's own fields, which Spring's Objenesis-built proxies never set."},
  {"front": "Which proxy does Spring Boot use by default for a bean that implements an interface?", "back": "A CGLIB subclass: Boot sets `proxyTargetClass=true` unless `spring.aop.proxy-target-class=false`."},
  {"front": "What does Quarkus ArC do with a bean's call to its own intercepted method?", "back": "It intercepts it (self-interception), a documented, non-standard CDI behaviour. Spring's proxy mode doesn't."},
  {"front": "Which Kotlin plugin opens Spring beans, and which opens JPA entities?", "back": "`kotlin-spring` (an all-open preset) for Spring annotations; `kotlin-jpa` for entities, which also adds constructors with no parameters."}
 ],
 "terms": [
  {"term": "Subclass proxy", "plain": "A generated subclass that overrides methods to add work around them; it works for classes, not only interfaces."},
  {"term": "Byte Buddy", "plain": "A library for generating and changing classes while a program runs; Hibernate and many tools build on it."},
  {"term": "Interceptor", "plain": "An object whose method runs in place of an intercepted method and decides when to call the original."},
  {"term": "CGLIB", "plain": "An older bytecode library, now unmaintained; Spring ships its own patched copy for class-based proxies."},
  {"term": "Objenesis", "plain": "A library that creates objects without running constructors; Spring uses it for CGLIB proxy objects."},
  {"term": "Client proxy", "plain": "ArC's `Foo_ClientProxy`: a subclass that forwards each call to the real bean instance for its scope."},
  {"term": "Self-interception", "plain": "Intercepting a call a bean makes to its own method. ArC supports it; Spring's proxy mode doesn't."},
  {"term": "all-open", "plain": "A Kotlin compiler plugin that makes classes with chosen annotations, and their members, non-final."}
 ],
 "explain_back": {
  "prompt": "A teammate says: \"Spring uses a CGLIB subclass, and a subclass overrides methods, so self-calls must be intercepted.\" Explain why that's wrong, why Quarkus behaves differently, and what Kotlin adds to the picture.",
  "answer": "Being a subclass only tells you which methods can be intercepted: the ones it can override. The question is which object runs the body. Spring's CGLIB proxy is a separate object that forwards each call to the target bean. The body runs on the target, where `this` is the target, so a call to `this.book()` never reaches the proxy. Methods the proxy can't override, `final` or `private` ones, run on the proxy object itself, whose fields Objenesis never set. Quarkus ArC generates an intercepted subclass that is the bean object itself, so `this.book()` goes to the overriding method and the interceptors run; its documentation calls this self-interception. Kotlin makes classes and members final by default, so without `open`, or the kotlin-spring or all-open plugin, there is nothing to override. Then Spring can't proxy the class at all, or quietly can't advise the method."
 },
 "deeper": {
  "minutes": 10,
  "body": "Byte Buddy can also change a class instead of extending it. `rebase(Clock.class)` keeps the original method body under a new private name, `now$original$...`, and generates a new `now` that can call it. The Javadoc likens it to \"creating a subclass where the subclass is later merged with the original class file\". `redefine(Clock.class)` replaces `now` and throws the original body away. Both produce a class with the original name, so you can only load the result where the original isn't loaded yet, or rename it, or, in a running JVM, use an agent. That's lesson 7, where Byte Buddy's `Advice` comes in. Advice copies your code into the existing method body instead of adding accessor methods and helper classes, which is what changing an already loaded class requires.\n\nThe subclass's helpers have a cost you can see. Each intercepted method gets an `$accessor$` twin so the interceptor can call the original, and `@SuperCall` creates a small `Callable` on every call. In this track's single JMH run on a shared 4-core machine, a Byte Buddy subclass with `@SuperCall` measured about 0.9 ns per call, against 0.8 ns for a direct call and about 4.3 ns for a JDK proxy. The numbers are noisy and only indicative, but the order is clear.\n\nQuarkus can intercept some static methods too. The CDI reference allows an interceptor binding on a non-private static method, with three limits: only bindings on the method itself count, private static methods are never intercepted, and `InvocationContext#getTarget()` returns `null`. For producer methods whose result needs interceptors, `InterceptionProxy` generates, at build time, a subclass that intercepts and forwards. The class must not be final, must not have non-private final methods, and needs a non-private constructor with no parameters. These are the subclass rules once again."
 },
 "sources": [
  {"title": "Spring Framework reference: Proxying mechanisms", "url": "https://docs.spring.io/spring-framework/reference/core/aop/proxying.html"},
  {"title": "Quarkus: Contexts and Dependency Injection reference (ArC)", "url": "https://quarkus.io/guides/cdi-reference"},
  {"title": "Byte Buddy README", "url": "https://github.com/raphw/byte-buddy/blob/master/README.md"},
  {"title": "kotlin-spring compiler plugin (Kotlin docs)", "url": "https://kotlinlang.org/docs/kotlin-spring-plugin.html"},
  {"title": "Hibernate ORM introduction: Interacting with the database (proxies, source)", "url": "https://raw.githubusercontent.com/hibernate/hibernate-orm/main/documentation/src/main/asciidoc/introduction/Interacting.adoc"}
 ]
}
# spread the correct answers over the option positions
for q, idx in zip(L["quiz"], [1, 2, 0, 3, 1]):
    right = q["options"].pop(q["answer"])
    q["options"].insert(idx, right)
    q["answer"] = idx
out = ROOT / "content/lessons/cls-05.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
