package workbench.functional.l02

/**
 * TODO 7: return a counter. Each call returns the next number: 1, 2, 3, ...
 * Two counters made by two calls of makeCounter never share a count.
 * It only has to work on one thread.
 */
fun makeCounter(): () -> Int = TODO("a local var, and a lambda that captures it")

/**
 * A counter that many consumer threads share, for example to number the payments they handle.
 *
 * It is broken. `count` is a captured var, so the compiler moves it into a kotlin.jvm.internal.Ref.LongRef
 * box with a plain, non-volatile field. `++count` from two threads is a read, an add and a write, and
 * updates get lost. The test runs it on 8 threads.
 *
 * TODO 8: fix it so the test passes every time. Keep the signature.
 */
fun makeSharedCounter(): () -> Long {
    var count = 0L
    return { ++count }
}
