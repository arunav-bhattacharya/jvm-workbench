import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/bytecode/src"
P = "java/workbench/bytecode/l04"
K = "kotlin/workbench/bytecode/l04"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :bytecode:demo -Pmain=workbench.bytecode.l04."


def demo(java, kt):
    return {"lang": "java", "title": f"{java}.java", "src": read(f"{lab}/demo/{P}/{java}.java"),
            "run": RUN + java, "file": f"{lab}/demo/{P}/{java}.java",
            "alt": {"lang": "kotlin", "title": f"{kt}.kt", "src": read(f"{lab}/demo/{K}/{kt}.kt"),
                    "run": RUN + kt + "Kt", "file": f"{lab}/demo/{K}/{kt}.kt"}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = """<svg viewBox="0 0 680 300" role="img" aria-label="Two ways a handler can run a default method. Forwarded to the target, the body's inner calls go to the target and skip the handler. Through invokeDefault, the body runs with this as the proxy, so both inner calls come back through the handler.">
<text class="t-s t-m" x="20" y="22">handler forwards with m.invoke(target, args)</text>
<rect class="box" x="20" y="34" width="90" height="40" rx="8"/>
<text class="t-s" x="65" y="59" text-anchor="middle">caller</text>
<rect class="box-a" x="140" y="34" width="90" height="40" rx="8"/>
<text class="t-s" x="185" y="59" text-anchor="middle">proxy</text>
<rect class="box" x="260" y="34" width="90" height="40" rx="8"/>
<text class="t-s" x="305" y="59" text-anchor="middle">handler</text>
<rect class="box" x="380" y="34" width="150" height="40" rx="8"/>
<text class="t-s t-code" x="455" y="59" text-anchor="middle">target.total</text>
<rect class="box-bad" x="550" y="34" width="110" height="40" rx="8"/>
<text class="t-s t-code" x="605" y="59" text-anchor="middle">this.minutes x2</text>
<line class="ln" x1="110" y1="54" x2="136" y2="54" marker-end="url(#arr)"/>
<line class="ln" x1="230" y1="54" x2="256" y2="54" marker-end="url(#arr)"/>
<line class="ln" x1="350" y1="54" x2="376" y2="54" marker-end="url(#arr)"/>
<line class="ln-bad" x1="530" y1="54" x2="546" y2="54" marker-end="url(#arr)"/>
<text class="t-s t-bad" x="605" y="94" text-anchor="middle">this = target</text>
<text class="t-s t-bad" x="455" y="94" text-anchor="middle">handler saw 1 call</text>
<text class="t-s t-m" x="20" y="152">handler runs it with invokeDefault(proxy, m, args)</text>
<rect class="box" x="20" y="164" width="90" height="40" rx="8"/>
<text class="t-s" x="65" y="189" text-anchor="middle">caller</text>
<rect class="box-a" x="140" y="164" width="90" height="40" rx="8"/>
<text class="t-s" x="185" y="189" text-anchor="middle">proxy</text>
<rect class="box" x="260" y="164" width="90" height="40" rx="8"/>
<text class="t-s" x="305" y="189" text-anchor="middle">handler</text>
<rect class="box-ok" x="380" y="164" width="150" height="40" rx="8"/>
<text class="t-s t-code" x="455" y="189" text-anchor="middle">Scenes.total</text>
<line class="ln" x1="110" y1="184" x2="136" y2="184" marker-end="url(#arr)"/>
<line class="ln" x1="230" y1="184" x2="256" y2="184" marker-end="url(#arr)"/>
<line class="ln" x1="350" y1="184" x2="376" y2="184" marker-end="url(#arr)"/>
<path class="ln-a" fill="none" d="M455 204 L455 240 L185 240 L185 208" marker-end="url(#arr)"/>
<text class="t-s t-a" x="320" y="258" text-anchor="middle">this.minutes(...) x2: this = proxy, back through the handler</text>
<text class="t-s t-ok" x="320" y="282" text-anchor="middle">handler saw 3 calls: total, minutes, minutes</text>
</svg>"""

GEN = """public final int costumes(java.lang.String) throws ;      // JDK 25, names shortened
   0: aload_0
   1: getfield      Proxy.h:InvocationHandler                   // 1. the handler
   4: aload_0                                                    // 2. the proxy itself
   5: getstatic     m3:Method                                    // 3. Method looked up once, in <clinit>
   8: iconst_1
   9: anewarray     Object                                       // 4. box the arguments into an Object[]
  12: dup
  13: iconst_0
  14: aload_1
  15: aastore
  16: invokeinterface InvocationHandler.invoke:(Object;Method;[Object;)Object
  21: checkcast     Integer                                      // 5. unbox the result
  24: invokevirtual Integer.intValue:()I
  27: ireturn
  28: athrow                                                     // Error, RuntimeException: rethrow as is
  29: new           UndeclaredThrowableException                 // anything else: wrap it
  ...
Exception table:
   from  to  target  type
     0   28    28    Class java/lang/Error
     0   28    28    Class java/lang/RuntimeException
     0   28    29    any"""

OPENING = """Picture a busy lead actor with a stand-in at the stage door. Every request meant for the actor goes to the stand-in first: a costume fitting, a photo, a note from the director. The stand-in writes each one down, tries again if the actor doesn't answer, and then passes it on. The actor's work doesn't change at all. The extra jobs happen at the door.

Java can put a stand-in like that in front of any interface, while your program runs. `java.lang.reflect.Proxy` writes a new class on the spot, and every call on it goes to one method of yours, an `InvocationHandler`. You met the pattern in Decorator and Proxy. In the last lesson, call sites linked to methods that already existed; this time the JDK writes a whole class.

The one-line handler, "pass every call on", looks finished after the first test. It quietly breaks `equals`, wraps exceptions twice, and retries steps that already worked. In this lesson, we'll build a stand-in by hand, read the class the JDK writes, sort out what the handler owes its callers, and decide who `this` is inside a default method. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_HAND = """final class HandProxy implements Wardrobe {
    private static final Method COSTUMES;                       // 1. looked up once
    static {
        try {
            COSTUMES = Wardrobe.class.getMethod("costumes", String.class);
        } catch (NoSuchMethodException e) {
            throw new NoSuchMethodError(e.getMessage());
        }
    }

    private final InvocationHandler h;
    HandProxy(InvocationHandler h) { this.h = h; }

    @Override
    public int costumes(String role) {
        try {
            return (Integer) h.invoke(this, COSTUMES, new Object[]{role});   // 2. box, ask the handler, unbox
        } catch (RuntimeException | Error e) {
            throw e;                                                      // 3. unchecked: as is
        } catch (Throwable t) {
            throw new UndeclaredThrowableException(t);                    // 4. undeclared checked: wrapped
        }
    }
    // ...the same for dressed, equals, hashCode and toString
}"""
K_HAND = """class HandProxy(private val h: InvocationHandler) : KWardrobe {
    override fun costumes(role: String): Int =
        try {
            h.invoke(this, COSTUMES, arrayOf(role)) as Int               // 2. box, ask the handler, unbox
        } catch (e: RuntimeException) {
            throw e                                                    // 3. unchecked: as is
        } catch (e: Error) {
            throw e
        } catch (t: Throwable) {
            throw UndeclaredThrowableException(t)                      // 4. undeclared checked: wrapped
        }
    // ...the same for dressed, equals, hashCode and toString

    companion object {
        private val COSTUMES = KWardrobe::class.java.getMethod("costumes", String::class.java)  // 1. once
    }
}"""

S0 = """The show program asks the theatre's wardrobe system how many costumes each role has. It talks to it through a small interface, `Wardrobe`, with one method, `costumes(role)`, and a default method `dressed(role)` that checks the count is above 0.

Let's first write a stand-in by hand, for this one interface. It holds one `InvocationHandler`: an object with a single method, `invoke(proxy, method, args)`, that receives every call. That's the stand-in's notebook. Each request arrives as one note: which method was called (a `java.lang.reflect.Method`, the object that describes a method) and its arguments, in an `Object[]`:

""" + pair(J_HAND, K_HAND) + """

Each method finds its `Method` object once and puts the arguments into an `Object[]`. Boxing turns primitive values such as `int` into objects such as `Integer` along the way. Then it asks the handler and unboxes the answer. That compiles and works: a test with a handler that always answers 3 printed `3`. Writing it by hand for forty methods on six interfaces is the kind of job nobody volunteers for twice, so the JDK writes it for you.

In *Decorator and Proxy* you passed a handler to `Proxy.newProxyInstance`. At that moment the JDK generated a class like `HandProxy`, for whichever interfaces you listed. Here's what `ProxyAnatomy` reports about it, on JDK 21 and JDK 25 alike:

```text
class      public final jdk.proxy1.$Proxy0
extends    java.lang.reflect.Proxy, implements [interface ...ProxyAnatomy$Wardrobe]
module     jdk.proxy1, hidden: false
fields     [m0, m1, m2, m3, m4]
methods    [costumes, dressed, equals, hashCode, proxyClassLookup, toString]
```

The `Proxy` Javadoc promises most of this. A proxy class is `final`, extends `java.lang.reflect.Proxy`, and implements exactly the interfaces you passed, in the same order. Its name isn't specified, but names that start with `$Proxy` are kept for proxy classes, and `Proxy.isProxyClass` recognizes it. The module `jdk.proxy1` and the counter in `$Proxy0` are details of the JDK, free to change.

Every generated method is `HandProxy.costumes`, written straight in bytecode. This is `costumes(String)` as JDK 25 generated it:

```text
""" + "{GEN}" + """
```

So every call loads the handler and the proxy, and fetches the `Method` object that the static initializer looked up once. (`m0` to `m2` are `hashCode`, `equals` and `toString`, then come your interface's methods.) It copies the arguments into a fresh `Object[]` and calls `invoke`. The result is cast back and unboxed. A `null` returned for a primitive return type becomes a `NullPointerException` at that unboxing step.

The exception table is the whole exception contract. `Error` and `RuntimeException` pass straight through, and so do checked exceptions that the interface method declares. Anything else gets wrapped in `UndeclaredThrowableException`. `costumes` declares nothing, so its last entry is `any`.

The Kotlin twin prints the same shape for a Kotlin interface. Proxies are a JVM feature, and kotlinc's interfaces are ordinary JVM interfaces. Since JDK 23, the JDK writes these classes with the ClassFile API; JDK 21 still used its internal copy of ASM, a library for writing class files, so its bytecode differs slightly in the exception handler.

**A JDK proxy turns every call into one `invoke` with a `Method` and an `Object[]`.**

Every call, then, lands in one place. Which calls, exactly, and what must the handler hand back?"""

# ---------------------------------------------------------------- section 1
J_FWD = """InvocationHandler h = (proxy, m, args) -> m.invoke(target, args);   // equals too"""
K_FWD = """val h = InvocationHandler { _, m, args -> m.invoke(target, *(args ?: emptyArray())) }   // equals too"""

S1 = """Three methods of `Object` reach the handler: `hashCode`, `equals` and `toString`, each with `method.getDeclaringClass() == Object.class`. The other public `Object` methods, such as `getClass`, `wait` and `notify`, are `final`, and the proxy doesn't override them. The stand-in can't lie about which class it is. For `hashCode` and other methods with no parameters, `args` is `null`, not an empty array.

What you do with `equals` matters. The company keeps its big props in a store across town, and the show program reaches it through an interface `PropStore`. The tempting handler for it forwards everything:

""" + pair(J_FWD, K_FWD) + """

Now `proxy.equals(proxy)` asks `target.equals(proxy)`. The real prop store has never heard of the proxy, so the answer is `false`. Ask the proxy whether it is itself, and it says no. The `ObjectMethodsDemo` shows what that costs:

```text
p.equals(p): false   (target.equals(p) was asked)
listeners.remove(p) after listeners.add(p): false, size still 1
HashSet.contains(p): true   (HashMap checks == before equals)
```

After `listeners.add(p)`, `listeners.remove(p)` returns `false`, and the proxy stays in the list. A `HashSet` happens to survive, because `HashMap` compares references with `==` before it calls `equals`. That's luck, not correctness.

Here the stand-in picture breaks, and it breaks on identity. Ask a human stand-in "are you the one I gave my note to?", and they answer for themselves. A careless handler passes even that question on to the actor. So answer `equals` and `hashCode` by the proxy's own identity (`proxy == args[0]`, `System.identityHashCode(proxy)`), or decide on purpose how two proxies compare.

The handler also owes the caller the right exceptions. The generated method rethrows unchecked exceptions and the checked exceptions its interface method declares, and wraps any other checked exception in `UndeclaredThrowableException`. `Method.invoke` adds a second layer of its own: whatever the target throws arrives wrapped in `InvocationTargetException`. A handler must catch that and rethrow `e.getCause()`. Otherwise the caller sees an `UndeclaredThrowableException`, wrapping an `InvocationTargetException`, wrapping the real error.

Kotlin makes the first rule easy to trip over. Kotlin has no checked exceptions (exceptions the compiler makes you catch or declare), so a Kotlin interface method declares none unless you write `@Throws`. A Kotlin implementation may still throw `IOException`, from a Java library it calls, because Kotlin doesn't check. A handler that unwraps correctly then produces `UndeclaredThrowableException`, and a Kotlin `catch (e: IOException)` around the call never matches. The demo's `status()` shows it. Add `@Throws(IOException::class)` to interface methods whose implementations can throw checked exceptions.

Two more rules from the Javadoc. Only interfaces can be proxied: passing a class fails with `IllegalArgumentException: ... is not an interface`. And if two interfaces declare the same method, the handler gets the `Method` from the first interface in your list, whichever one the caller used.

**Answer `equals` and `hashCode` by the proxy's identity, and unwrap `InvocationTargetException`.**

`Object` methods and exceptions are two of the special cases. The third hides in plain sight: default methods."""

# ---------------------------------------------------------------- section 2
J_INVDEF = """if (method.isDefault()) {
    return InvocationHandler.invokeDefault(proxy, method, args);   // the body runs with this = proxy
}"""
K_INVDEF = """if (method.isDefault) {
    return@InvocationHandler InvocationHandler.invokeDefault(proxy, method, *(args ?: emptyArray()))
}"""

S2 = """*Decorator and Proxy* showed the self-invocation trap. The real stockroom's `pickBoth` called `pick` through `this`, and `this` was the real object, so the proxy never saw the inner calls. Self-invocation is a method calling another method of the same object through `this`. In the theatre, it's the actor talking to themselves: nothing passes the stage door. Default methods give you a choice about it.

`Scenes` is the interface the show program uses to ask how long a scene runs. It has an abstract `minutes(scene)` and a default method `total(a, b)` that calls `minutes` twice, on `this`. If the handler forwards `total` with `method.invoke(target, args)`, the default body runs on the target. Its `this` is the target, and its two inner calls skip the proxy. `DefaultMethodsDemo` logs `[total]`.

JDK 16 added `InvocationHandler.invokeDefault(proxy, method, args)`. It runs the interface's default body with `this` set to the proxy, so every call the body makes comes back through the handler:

""" + pair(J_INVDEF, K_INVDEF) + """

Now the demo logs `[total, minutes, minutes]`. The proxy doesn't even need a target. A handler that answers the abstract methods itself, and sends default methods to `invokeDefault`, is a complete implementation: the demo's target-less proxy answers 5 for every scene, and `total` comes out at 10. Calling `invokeDefault` on an abstract method throws `IllegalArgumentException`, and on a default method your code isn't allowed to reach, it throws `IllegalAccessException`.

Kotlin interfaces work too. With the labs' JVM target 21, kotlinc 2.4.21 compiles an interface function that has a body to a real JVM `default` method, plus a `DefaultImpls` class for older callers. `method.isDefault` is `true`, and `invokeDefault` runs the Kotlin body: the Kotlin twin prints the same three calls.

This choice decides whether a retry proxy is safe, a proxy that calls again when a call fails. The theatre's seat booking runs on another computer, reached through an interface `SeatDesk`. `hold(show, guest)` keeps a seat aside for a guest, `confirm(holdId)` confirms it, and a default method does both: `return confirm(hold(show, guest));`.

Suppose your handler treats `holdAndConfirm` like any other method and retries it when it fails. The first attempt holds a seat, then the confirmation fails, so the handler retries the whole method, and the second attempt holds a second seat. Run default methods through `invokeDefault` and retry only the abstract calls inside them. A failed confirmation is then retried as a confirmation, and the hold that already worked stays at one. The lab tests exactly this.

**Run default methods with `invokeDefault`. Never retry one as a whole.**

That's the handler's logic complete. What's left is the price: of making the class, and of every call through it."""

# ---------------------------------------------------------------- section 3
S3 = """Generating a class is the expensive part, and the JDK does it only once. `Proxy` caches proxy classes per class loader, keyed by the ordered list of interfaces. Ten thousand `newProxyInstance` calls with the same loader and interfaces generate one class and construct ten thousand small objects. Listing the same interfaces in a different order generates a second class, as `ProxyAnatomy` showed with `$Proxy1` and `$Proxy2`.

Each class loader gets one dynamic module for its proxies, a module the JDK creates while the program runs. On the runs for this track, proxies for app-loader interfaces landed in `jdk.proxy1`, and a `Runnable` proxy created with the bootstrap loader (`null`) landed in `jdk.proxy2`. If any interface isn't public, the proxy class goes into that interface's package instead, and isn't public either (`demo.$Proxy8` in one run). Calling `Constructor.newInstance` on a proxy class in a dynamic module throws `IllegalAccessException`. Use `newProxyInstance`, because `Proxy.getProxyClass` is deprecated.

The cost of each call is the bytecode from the first section: an `Object[]`, boxing, a call to the handler, and whatever the handler does. JMH, the JDK project's tool for timing small pieces of code, measured `add(3, 4)` four ways on JDK 25. This was one run on a shared 4-core machine, with one fork and wide error bars:

| Call | ns per call |
|---|---|
| direct | 0.83 |
| Byte Buddy subclass with `@SuperCall` (lesson 5) | 0.88 |
| JDK proxy, handler calls `method.invoke(target, args)` | 4.3 |
| plain `Method.invoke` with boxing | 11.8 |

Read the order, not the decimals. A few nanoseconds per call is nothing next to a 120 ms call to the seat desk on another computer. It does show up in a loop that calls a proxied interface millions of times, and there a subclass proxy or plain code wins.

You can save the generated class and read it yourself. `-Djdk.proxy.ProxyGenerator.saveGeneratedFiles=true` writes it to `jdk/proxy1/$Proxy0.class` under the current folder. On JDK 21 that just works. On the JDK 24 to 27 builds tested for this track, JDK 25 included, the JDK writes the first file, and then `newProxyInstance` throws `NullPointerException`. The JDK source explains it: a `return null;` that used to sit inside a `doPrivileged` lambda now returns from `generateProxyClass` itself. The file is still written, so you can read it on any of them.

Here's the limit of today's tool, and it's a hard one. A JDK proxy can only implement interfaces. A class with no interface, or a Kotlin class that is `final` by default, can't have a stand-in this way at all."""

L = {
 "id": "cls-04",
 "title": "Dynamic proxies with java.lang.reflect.Proxy",
 "minutes": 40,
 "goal": "By the end you can read the class that Proxy.newProxyInstance generates, write a handler that gets equals, exceptions and default methods right (including InvocationHandler.invokeDefault), and predict when a proxy class is generated and what each call costs.",
 "opening": OPENING,
 "warmup": {
  "q": "A JDK proxy for `interface Scenes { int minutes(String s); default int total(String a, String b) { return minutes(a) + minutes(b); } }` has a handler that logs each call and then does `return method.invoke(target, args);`. A caller runs `proxy.total(\"prologue\", \"duel\")`. How many calls does the handler log?",
  "options": [
   "1: only `total`",
   "3: `total`, then `minutes` twice",
   "2: `minutes` twice, because default methods never reach the handler",
   "0: default methods bypass the proxy"
  ],
  "answer": 0,
  "why": "`total` reaches the handler like any interface method. The handler then runs the default body on the target, where `this` is the target, so the two `minutes` calls never pass through the proxy. Run the body with `InvocationHandler.invokeDefault(proxy, method, args)` instead, and `this` is the proxy: the handler then logs 3 calls. The section on default methods shows both runs."
 },
 "sections": [
  {
   "h": "Building a stand-in by hand, then reading the one the JDK writes",
   "body": S0,
   "try": {
    "title": "Take a proxy apart",
    "minutes": 4,
    "steps": [
     "Read `ProxyAnatomy` (or `ProxyAnatomy.kt`). Before running it, predict which of the five calls in part 2 reach the handler.",
     "Run it. Check the class name, its fields and methods, and the list the handler saw.",
     "Look at part 3: why do `{Wardrobe, Audited}` and `{Audited, Wardrobe}` get different class names?"
    ],
    "code": demo("ProxyAnatomy", "ProxyAnatomy"),
    "expect": "`public final jdk.proxy1.$Proxy0`, extending `java.lang.reflect.Proxy` in module `jdk.proxy1`, with fields `m0` to `m4`. The handler saw `Wardrobe.costumes`, `Object.toString`, `Object.hashCode` and `Object.equals`, but not `getClass()`. The same interface again gives the same class. The two orderings give `$Proxy1` and `$Proxy2`, because the class implements its interfaces in the order you list them, so the cache keys on the order too."
   },
   "refs": [
    {"title": "Proxy (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/reflect/Proxy.html", "kind": "docs"}
   ]
  },
  {
   "h": "What reaches the handler, and what the handler owes the caller",
   "body": S1,
   "try": {
    "title": "Break equals, then the exception contract",
    "minutes": 4,
    "steps": [
     "Run `ObjectMethodsDemo` (or the Kotlin twin) and read its five lines.",
     "In `forwardingEverything`, answer `equals` before the `try`: `if (m.getName().equals(\"equals\")) return proxy == args[0];` (in Kotlin, rename the lambda's first parameter from `_` to `proxy`, then add `if (m.name == \"equals\") return@newProxyInstance proxy === args[0]`). Run it again.",
     "In the Kotlin twin, remove `@Throws(IOException::class)` from `fetch` and predict what the `catch (e: IOException)` block does now. Run it."
    ],
    "code": demo("ObjectMethodsDemo", "ObjectMethodsDemo"),
    "expect": "First run: `p.equals(p): false`, `listeners.remove(p) ... false, size still 1`, `HashSet.contains(p): true`, the declared `IOException` passing through (`prop store took longer than 120 ms`), and `UndeclaredThrowableException` for `status()`. After the `equals` fix, `p.equals(p)` is `true`, `remove` returns `true` and the list is empty (so the set built from it is empty too). Without `@Throws`, the Kotlin `fetch` call ends the program with an `UndeclaredThrowableException` whose cause is the `IOException`: the `catch` no longer matches."
   },
   "refs": [
    {"title": "InvocationHandler (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/reflect/InvocationHandler.html", "kind": "docs"}
   ]
  },
  {
   "h": "Default methods: the handler decides who this is",
   "body": S2,
   "figure": {"svg": FIG, "caption": "Forwarding a default method to the target hides its inner calls, like an actor talking to themselves. invokeDefault runs the body on the proxy, so the handler sees each call."},
   "try": {
    "title": "Count the handler calls",
    "minutes": 4,
    "steps": [
     "Read `DefaultMethodsDemo`. Predict the `handler saw` list for both runs, and the total for the target-less proxy.",
     "Run it (or the Kotlin twin).",
     "Change `RealScenes.minutes` to throw `IllegalStateException` for `\"duel\"` and run it again. What does the first run's log hold when it fails?"
    ],
    "code": demo("DefaultMethodsDemo", "DefaultMethodsDemo"),
    "expect": "`forward to target: total=120, handler saw [total]`, then `invokeDefault:     total=120, handler saw [total, minutes, minutes]`, then `no target:         total=10` (two answers of 5), then `IllegalArgumentException`. With the exception for `\"duel\"`, the program stops in the first run. Its stack trace shows `RealScenes.minutes` called from `Scenes.total` on the target, and the handler never logged a `minutes` call: a retry or a timer in the handler couldn't have seen the failing call. In the `invokeDefault` version, the same failure would pass through the handler as the second `minutes` call."
   }
  },
  {
   "h": "One class per loader and interface list, and a few nanoseconds per call",
   "body": S3,
   "try": {
    "title": "Read the class the JDK wrote",
    "minutes": 4,
    "steps": [
     "Run `ProxyAnatomy` once with Gradle so its classes exist. Then, from `labs/`, run the commands below. They work in a temporary folder, because the flag writes into the current one.",
     "On JDK 24 or later, expect a `NullPointerException` after the first file is written. Carry on with `javap`.",
     "Find `costumes` and compare it with the listing in the first section. Then find the static initializer: where does it look up `m3`?"
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "D=$PWD/bytecode/build/classes/java/demo\ncd \"$(mktemp -d)\"\njava -Djdk.proxy.ProxyGenerator.saveGeneratedFiles=true -cp \"$D\" workbench.bytecode.l04.ProxyAnatomy\njavap -c -p 'jdk/proxy1/$Proxy0.class' | less", "run": ""},
    "expect": "`costumes` loads `h`, the proxy and `m3`, builds a one-element `Object[]`, calls `InvocationHandler.invoke`, then runs `checkcast Integer` and `intValue`. The static initializer calls `Class.getMethod` for `hashCode`, `equals`, `toString`, `costumes` and `dressed`, and stores them in `m0` to `m4`. For the interface's methods, it first finds `Wardrobe` by name with `Class.forName(name, false, loader)`; JDK 21 does that for `Object` too. On JDK 21 the program also prints its normal output. On JDK 24 and later, it stops with the NullPointerException after writing `$Proxy0.class`."
   },
   "refs": [
    {"title": "ProxyGenerator.java at jdk-25-ga (OpenJDK source)", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/reflect/ProxyGenerator.java", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "A tracing proxy in Java and Kotlin",
  "java": {"title": "Tracing.java", "src": "@SuppressWarnings(\"unchecked\")\nstatic <T> T tracing(Class<T> iface, T target, List<String> log) {\n    InvocationHandler h = (proxy, m, args) -> {\n        if (m.getDeclaringClass() == Object.class) {          // 1. identity, not the target's\n            return switch (m.getName()) {\n                case \"equals\" -> proxy == args[0];\n                case \"hashCode\" -> System.identityHashCode(proxy);\n                default -> \"Tracing[\" + target + \"]\";\n            };\n        }\n        log.add(m.getName());\n        if (m.isDefault()) return InvocationHandler.invokeDefault(proxy, m, args);  // 2. this = proxy\n        try {\n            return m.invoke(target, args);                    // 3. args is null for no-arg methods\n        } catch (InvocationTargetException e) {\n            throw e.getCause();                               // 4. the target's own exception\n        }\n    };\n    return (T) Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[]{iface}, h);\n}"},
  "kotlin": {"title": "Tracing.kt", "src": "inline fun <reified T : Any> tracing(target: T, log: MutableList<String>): T =\n    Proxy.newProxyInstance(T::class.java.classLoader, arrayOf(T::class.java)) { proxy, m, args ->\n        val a = args ?: emptyArray()                          // 3. null for no-arg methods\n        when {\n            m.declaringClass == Any::class.java -> when (m.name) {   // 1. identity\n                \"equals\" -> proxy === a[0]\n                \"hashCode\" -> System.identityHashCode(proxy)\n                else -> \"Tracing[$target]\"\n            }\n            else -> {\n                log += m.name\n                if (m.isDefault) InvocationHandler.invokeDefault(proxy, m, *a)   // 2. this = proxy\n                else try {\n                    m.invoke(target, *a)\n                } catch (e: InvocationTargetException) {\n                    throw e.cause!!                           // 4. the target's own exception\n                }\n            }\n        }\n    } as T"},
  "note": "Same JVM mechanism, same four cases. The Kotlin version is shorter because `reified T` reads `T::class.java` itself, so callers write `tracing(desk, log)`. Two Kotlin-specific traps sit in it. `args` is a nullable Java array, `null` for methods with no parameters, so spreading it directly (`*args`) throws `NullPointerException` on `hashCode()`. And Kotlin interfaces declare no checked exceptions unless you add `@Throws`, so an `IOException` from a Java library, which the handler rethrows correctly, still reaches Kotlin callers as `UndeclaredThrowableException`."
 },
 "worked": {
  "title": "A test double for SeatDesk with no implementation class",
  "steps": [
   {"say": "A test needs a `SeatDesk` that returns canned answers and records what was called, and you don't want to write a class with every method. A test double is a stand-in built for a test. A proxy with no target can be one. Start with the cases every handler needs.", "code": "static SeatDesk fakeDesk(Map<String, Object> answers, List<String> calls) {\n    InvocationHandler h = (proxy, m, args) -> {\n        // 1. Object methods: identity, so the fake behaves in collections\n        if (m.getDeclaringClass() == Object.class) {\n            return switch (m.getName()) {\n                case \"equals\" -> proxy == args[0];\n                case \"hashCode\" -> System.identityHashCode(proxy);\n                default -> \"FakeDesk\" + answers.keySet();\n            };\n        }\n        // 2. default methods: run the real interface body, which calls back through this handler\n        if (m.isDefault()) return InvocationHandler.invokeDefault(proxy, m, args);\n        // 3. abstract methods: record the call and return the canned answer\n        calls.add(m.getName() + Arrays.toString(args));\n        if (!answers.containsKey(m.getName())) throw new UnsupportedOperationException(m.getName());\n        return answers.get(m.getName());\n    };\n    return (SeatDesk) Proxy.newProxyInstance(\n            SeatDesk.class.getClassLoader(), new Class<?>[]{SeatDesk.class}, h);\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "fun fakeDesk(answers: Map<String, Any>, calls: MutableList<String>): SeatDesk =\n    Proxy.newProxyInstance(SeatDesk::class.java.classLoader, arrayOf(SeatDesk::class.java)) { proxy, m, args ->\n        val a = args ?: emptyArray()\n        when {\n            // 1. Object methods: identity, so the fake behaves in collections\n            m.declaringClass == Any::class.java -> when (m.name) {\n                \"equals\" -> proxy === a[0]\n                \"hashCode\" -> System.identityHashCode(proxy)\n                else -> \"FakeDesk${answers.keys}\"\n            }\n            // 2. default methods: run the real interface body, which calls back through this handler\n            m.isDefault -> InvocationHandler.invokeDefault(proxy, m, *a)\n            // 3. abstract methods: record the call and return the canned answer\n            else -> {\n                calls += m.name + a.contentToString()\n                answers[m.name] ?: throw UnsupportedOperationException(m.name)\n            }\n        }\n    } as SeatDesk"},
   {"say": "Use it. The interesting call is the default method: the fake has no code for `holdAndConfirm`, yet the interface's own body runs, and its two inner calls are recorded in order. A run of this code printed `confirmed hold-hamlet [hold[Hamlet, ana], confirm[hold-hamlet]]`. That works only because of `invokeDefault`: forwarding to a target isn't possible here, since there is no target.", "code": "List<String> calls = new ArrayList<>();\nSeatDesk desk = fakeDesk(\n        Map.of(\"hold\", \"hold-hamlet\", \"confirm\", \"confirmed hold-hamlet\"), calls);\n\nString result = desk.holdAndConfirm(\"Hamlet\", \"ana\");   // 4. exercise the default\n\nassertThat(result).isEqualTo(\"confirmed hold-hamlet\");\nassertThat(calls).containsExactly(\"hold[Hamlet, ana]\", \"confirm[hold-hamlet]\");", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "val calls = mutableListOf<String>()\nval desk = fakeDesk(mapOf(\"hold\" to \"hold-hamlet\", \"confirm\" to \"confirmed hold-hamlet\"), calls)\n\nval result = desk.holdAndConfirm(\"Hamlet\", \"ana\")   // 4. exercise the default\n\nassertThat(result).isEqualTo(\"confirmed hold-hamlet\")\nassertThat(calls).containsExactly(\"hold[Hamlet, ana]\", \"confirm[hold-hamlet]\")"},
   {"say": "Check the edges before you trust it. A canned answer of the wrong type fails at the proxy's `checkcast`, with a `ClassCastException` from the generated method rather than from your handler. A missing answer for a method returning `int` would be `null`, and the proxy's unboxing would turn that into a `NullPointerException`, so the handler throws a clear `UnsupportedOperationException` instead. And this fake works for one interface only. Mocking libraries, which build test doubles for you, grow the same idea with argument matchers and support for classes.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A retrying, timing proxy for the seat desk",
  "minutes": 15,
  "files": [
   "labs/bytecode/src/main/java/workbench/bytecode/l04/ResilientProxy.java",
   "labs/bytecode/src/main/java/workbench/bytecode/l04/RetryPolicy.java",
   "labs/bytecode/src/main/java/workbench/bytecode/l04/CallRecorder.java"
  ],
  "run": "./gradlew :bytecode:test --tests 'workbench.bytecode.l04.*'",
  "steps": [
   "Run the tests once. All seven fail. Read `SeatDesk` and the `FakeDesk` in the test: it fails a scripted number of calls and counts every one. `RetryPolicy` says how many attempts a call gets and which failures are worth another try, and `CallRecorder` receives one line per finished call.",
   "In `ResilientProxy.wrap`, create the proxy with `Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[]{iface}, handler)` and return `iface.cast(...)`.",
   "Write the handler's first two cases: `Object` methods answered by identity and `\"Resilient[\" + target + \"]\"`, then default methods through `InvocationHandler.invokeDefault`.",
   "Write the retry loop: read the clock once, call `method.invoke(target, args)`, and on `InvocationTargetException` take `getCause()`. Try again while attempts are left and `policy.retries(cause)` is true. Record `iface.getSimpleName() + \".\" + method.getName()` with the attempt count and `end - start` once, when the call ends.",
   "Run the tests until all seven pass. Then read `defaultMethodShellIsNotRetried` and say out loud why the desk saw one hold."
  ],
  "hints": [
   "The order of the cases matters. `equals` is not a default method, but check `Object` methods first anyway, so nothing else ever sees them.",
   "The fake clock moves 5 ms per read. If the recorded time isn't `5ms`, you're reading the clock more than twice per call.",
   "`throw cause;` compiles because `InvocationHandler.invoke` is declared `throws Throwable`. Because the cause is the target's own exception, the generated method lets `DeskUnavailableException` through: `hold` declares it."
  ],
  "done_when": "All seven tests in `ResilientProxyTest` pass."
 },
 "drill": {
  "title": "The four cases from memory",
  "minutes": 5,
  "prompt": "Close the page. Write an `InvocationHandler` that times each call of an interface and reports the method name, handling the four cases in the right order: `Object` methods, default methods, the timed call, and exceptions. Then check your version against the answer. Which case did you forget?",
  "answer": {
   "lang": "java",
   "src": "InvocationHandler h = (proxy, m, args) -> {\n    if (m.getDeclaringClass() == Object.class) {                        // 1. Object methods\n        return switch (m.getName()) {\n            case \"equals\" -> proxy == args[0];\n            case \"hashCode\" -> System.identityHashCode(proxy);\n            default -> \"Timed[\" + target + \"]\";\n        };\n    }\n    if (m.isDefault()) return InvocationHandler.invokeDefault(proxy, m, args);  // 2. defaults: this = proxy\n    long t0 = System.nanoTime();\n    try {\n        return m.invoke(target, args);                                  // 3. the timed call\n    } catch (InvocationTargetException e) {\n        throw e.getCause();                                             // 4. unwrap\n    } finally {\n        timings.record(m.getName(), System.nanoTime() - t0);\n    }\n};",
   "alt": {"lang": "kotlin", "src": "val h = InvocationHandler { proxy, m, args ->\n    val a = args ?: emptyArray()\n    if (m.declaringClass == Any::class.java) {                          // 1. Object methods\n        return@InvocationHandler when (m.name) {\n            \"equals\" -> proxy === a[0]\n            \"hashCode\" -> System.identityHashCode(proxy)\n            else -> \"Timed[$target]\"\n        }\n    }\n    if (m.isDefault) return@InvocationHandler InvocationHandler.invokeDefault(proxy, m, *a)  // 2. defaults\n    val t0 = System.nanoTime()\n    try {\n        m.invoke(target, *a)                                            // 3. the timed call\n    } catch (e: InvocationTargetException) {\n        throw e.cause!!                                                 // 4. unwrap\n    } finally {\n        timings.record(m.name, System.nanoTime() - t0)\n    }\n}"}
  }
 },
 "recap": [
  "`Proxy.newProxyInstance` generates a `public final $ProxyN extends Proxy` that implements exactly your interfaces, in order. Each method boxes its arguments into an `Object[]` and calls `h.invoke(proxy, Method, args)`.",
  "`hashCode`, `equals` and `toString` reach the handler; `getClass` doesn't. Answer `equals` and `hashCode` by the proxy's identity, or collections can't find the proxy.",
  "Unchecked exceptions and declared checked exceptions pass through; any other checked exception becomes `UndeclaredThrowableException`. Unwrap `InvocationTargetException`, and use `@Throws` on Kotlin interfaces.",
  "`InvocationHandler.invokeDefault` (JDK 16) runs a default body with `this` = proxy, so its inner calls come back through the handler. Never retry a default method as a whole: retry the abstract calls inside it.",
  "Proxy classes are cached per loader and ordered interface list, in one `jdk.proxyN` module per loader. A call costs a few nanoseconds: nothing next to a network call, visible in tight loops.",
  "The limit: a JDK proxy can only implement interfaces. A class with no interface, or a `final` Kotlin class, can't be wrapped this way."
 ],
 "closing": "We started with a stand-in at the stage door who takes every request for an actor, does a little extra, and passes it on. The JDK builds that stand-in as a real class: every call becomes one `invoke`, the handler must answer `equals` for itself and unwrap exceptions, and `invokeDefault` decides that `this` is the proxy.\n\nNow search your code for `InvocationHandler` or `newProxyInstance`, and check each handler for the four cases: `Object` methods, default methods, the real work, and an unwrapping `catch`.\n\nNext, we'll stand in front of classes that have no interface at all. How do Byte Buddy, Spring and Quarkus build a stand-in by writing a subclass?",
 "quiz": [
  {
   "q": "A handler does `return method.invoke(target, args)` for every method, unwrapping exceptions. A listener proxy is added to an `ArrayList` and later removed with `listeners.remove(proxy)`. What happens?",
   "options": [
    "It's removed: `remove` compares references",
    "`remove` returns `false` and the proxy stays, because `proxy.equals(proxy)` asked `target.equals(proxy)`, which is false",
    "It throws `UndeclaredThrowableException`",
    "It's removed, but only after the JIT compiles `equals`"
   ],
   "answer": 1,
   "why": "`ArrayList.remove(Object)` calls `equals` on each element, and the proxy forwards `equals` to the target, which knows nothing about the proxy. A `HashSet` would happen to work, because `HashMap` checks `==` first. The fix is identity in the handler: `proxy == args[0]`."
  },
  {
   "q": "Kotlin: `interface PropClient { fun fetch(): Prop }`, implemented by a Kotlin class whose `fetch()` calls a Java library that throws `IOException`. A JDK proxy around it unwraps `InvocationTargetException` correctly. A Kotlin caller wraps the call in `catch (e: IOException)`. What happens when the prop store is down?",
   "options": [
    "The `catch` runs: Kotlin has no checked exceptions, so anything goes",
    "The caller gets `UndeclaredThrowableException`: the interface method declares no `IOException`, so the generated proxy method wraps it",
    "The caller gets `InvocationTargetException`",
    "It doesn't compile"
   ],
   "answer": 1,
   "why": "The generated method only lets through unchecked exceptions and the checked exceptions its interface method declares. A Kotlin interface declares none unless you write `@Throws(IOException::class)`. With that annotation, the `IOException` reaches the caller unchanged and the `catch` matches."
  },
  {
   "q": "A program creates a new JDK proxy around a `SeatDesk` for every booking: 50,000 bookings an hour, the same class loader, the same single interface. How many proxy classes does the JVM generate?",
   "options": ["50,000, one per proxy", "One, then each booking only constructs a small proxy object", "One per thread", "None: proxies are hidden classes that aren't counted"],
   "answer": 1,
   "why": "`Proxy` caches the generated class per class loader, keyed by the ordered interface list. Later calls only construct an instance. Listing the interfaces in a different order would generate a second class. Proxy classes are not hidden: `isHidden()` is false."
  },
  {
   "q": "Your retry proxy retries any method that throws `DeskUnavailableException`, including the default method `holdAndConfirm()`, which calls `hold` then `confirm`, and it forwards default methods with `method.invoke(target, args)`. `confirm` fails once. What does the seat desk see?",
   "options": [
    "One hold and two confirms",
    "Two holds and two confirms: the whole default method ran again",
    "One hold and one confirm",
    "Nothing: default methods can't be proxied"
   ],
   "answer": 1,
   "why": "The default body runs on the target, so neither inner call is retried on its own. When `confirm` fails, the exception escapes the whole `holdAndConfirm`, and the handler retries all of it, the hold included. With `invokeDefault` and retries only on abstract methods, the desk sees one hold and two confirm attempts."
  },
  {
   "q": "From *Decorator and Proxy*: `RealStockroom.pickBoth` calls `pick` twice through `this`. A tracing JDK proxy stands in front of it and forwards every call to the target. A caller runs `proxy.pickBoth(\"tea\", \"jam\")`. How many `pick` calls does the proxy record?",
   "options": ["0: the proxy sees only `pickBoth`", "2", "1", "It depends on whether the JIT has compiled `pick`"],
   "answer": 0,
   "why": "`pickBoth` is a method of the target class, so its body runs on the target, and `this.pick` is a plain call on the target that never touches the proxy. That's the self-invocation trap. Only when `pickBoth` is an interface default method run with `invokeDefault` does `this` become the proxy.",
   "from": "pat-05"
  }
 ],
 "flashcards": [
  {"front": "What class does `Proxy.newProxyInstance` generate for one interface?", "back": "A `public final` class such as `jdk.proxy1.$Proxy0` that extends `java.lang.reflect.Proxy` and implements exactly the given interfaces, in order."},
  {"front": "Which `Object` methods reach an InvocationHandler?", "back": "`hashCode`, `equals` and `toString`, with `getDeclaringClass() == Object.class`. Not `getClass`, `wait` or `notify`."},
  {"front": "What is `args` in `invoke(proxy, method, args)` for a method with no parameters?", "back": "`null`, not an empty array. In Kotlin, use `args ?: emptyArray()` before spreading it."},
  {"front": "A handler throws a checked exception that the interface method doesn't declare. What does the caller get?", "back": "`UndeclaredThrowableException`, with the checked exception as its cause."},
  {"front": "What does `InvocationHandler.invokeDefault(proxy, m, args)` do differently from `m.invoke(target, args)`?", "back": "It runs the interface's default body with `this` = the proxy, so the body's inner calls come back through the handler. (JDK 16.)"},
  {"front": "When does `Proxy` generate a new class?", "back": "Once per class loader and ordered interface list. `{A, B}` and `{B, A}` are two classes."},
  {"front": "Why must a proxy answer `equals` itself?", "back": "Forwarding it makes `proxy.equals(proxy)` ask `target.equals(proxy)`, which is false, so lists can't find or remove the proxy."}
 ],
 "terms": [
  {"term": "Dynamic proxy", "plain": "An object of a class generated at run time that implements given interfaces and sends every call to one handler."},
  {"term": "InvocationHandler", "plain": "The single `invoke(proxy, method, args)` method that receives every call made on a JDK proxy."},
  {"term": "UndeclaredThrowableException", "plain": "The unchecked wrapper a proxy throws when its handler throws a checked exception that the method doesn't declare."},
  {"term": "InvocationTargetException", "plain": "The wrapper `Method.invoke` puts around whatever the called method threw. Unwrap it with `getCause()`."},
  {"term": "invokeDefault", "plain": "`InvocationHandler.invokeDefault`: runs an interface's default method body on the proxy itself (JDK 16)."},
  {"term": "Self-invocation", "plain": "A method calling another method of the same object through `this`, which goes straight past any proxy in front of it."},
  {"term": "Dynamic module", "plain": "A module such as `jdk.proxy1` that the JDK creates per class loader, while the program runs, to hold proxy classes."}
 ],
 "explain_back": {
  "prompt": "A teammate wants to wrap every client of a remote service in a JDK proxy that retries on timeouts. Explain what the JDK generates, the four cases their handler must handle, and the one retry rule that keeps a default method like `holdAndConfirm` from holding two seats.",
  "answer": "`Proxy.newProxyInstance` generates one `final` class per class loader and interface list. Each of its methods boxes the arguments into an `Object[]` and calls the handler with the proxy and a cached `Method`. The handler must first answer `equals`, `hashCode` and `toString` itself, by the proxy's identity, or collections stop finding the proxy. Second, it must run default methods with `InvocationHandler.invokeDefault`, so the body runs with `this` as the proxy and each inner call comes back through the handler. Third, it calls the target with `method.invoke` and retries only the failures the policy names, such as a timeout. Fourth, it rethrows `InvocationTargetException.getCause()`, so callers get the service's own exception and not an `UndeclaredThrowableException`. The retry rule: never retry a default method as one unit. Retry the abstract calls inside it, so a failed confirm is retried as a confirm, and the hold that already worked isn't sent again."
 },
 "deeper": {
  "minutes": 10,
  "body": "Three corners of `Proxy` that the lesson skipped.\n\nModules and visibility. If every interface is public and in an exported package, the proxy class is public, in an unconditionally exported but non-open package of a dynamic module. If any interface isn't public, the proxy class isn't public either, and goes into that interface's package and module, so all non-public interfaces must share one package. If an interface is in a package its module doesn't export, the proxy goes into a non-exported package of a dynamic module. In every dynamic-module case, `Constructor.newInstance` on the proxy class throws `IllegalAccessException`, which is why `Proxy.getProxyClass` is deprecated.\n\nWhat can fail at creation. `newProxyInstance` throws `IllegalArgumentException` when an element isn't a non-hidden, non-sealed interface, when an interface appears twice, when an interface isn't visible by name through the loader you pass (`Class.forName(i.getName(), false, loader) != i`), when two interfaces have a method with the same signature and incompatible return types, or when you pass more than 65,535 interfaces. The loader rule is the one you'll meet: in a plugin system or a test runner, pass the loader that defined the interface (`iface.getClassLoader()`), not some other loader that holds a second copy of it (lesson 1).\n\nThe caches. `Proxy` keeps the constructors in a `ClassLoaderValue`, so the cache entry goes away with the loader. A second cache backs `isProxyClass`. And a `ClassValue` of `ConcurrentHashMap<Method, MethodHandle>` holds the method handles behind `invokeDefault`, so only the first call of each default method pays for the lookup.\n\nThe `saveGeneratedFiles` crash from the last section is easy to see in the source. At jdk-21-ga, `generateProxyClass` wrote the file inside `AccessController.doPrivileged(new PrivilegedAction<>() { ... return null; })`, and that `return null` belonged to the inner block. At jdk-24-ga, the release that permanently disabled the Security Manager, the `doPrivileged` wrapper is gone, and the same `return null;` now returns from `generateProxyClass` itself, so `defineClass` receives `null` bytes. That matches the message JDK 25 printed: `Cannot read the array length because \"b\" is null`."
 },
 "sources": [
  {"title": "Proxy (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/reflect/Proxy.html"},
  {"title": "InvocationHandler (Java SE 25 API), including invokeDefault", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/reflect/InvocationHandler.html"},
  {"title": "Proxy.java at jdk-25-ga (OpenJDK source)", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/reflect/Proxy.java"},
  {"title": "ProxyGenerator.java at jdk-25-ga (OpenJDK source)", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/reflect/ProxyGenerator.java"}
 ]
}
# the generated-method listing goes into the first section
L["sections"][0]["body"] = L["sections"][0]["body"].replace("{GEN}", GEN)
# spread the correct answers over the option positions
for q, idx in zip(L["quiz"], [1, 3, 0, 2, 0]):
    right = q["options"].pop(q["answer"])
    q["options"].insert(idx, right)
    q["answer"] = idx
out = ROOT / "content/lessons/cls-04.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
