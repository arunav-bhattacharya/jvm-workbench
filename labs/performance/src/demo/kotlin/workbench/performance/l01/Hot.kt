package workbench.performance.l01

// Kotlin twin of Hot.java: the same program, so you can compare what the JIT does with Kotlin bytecode.
// Run without arguments: it starts a second JVM with -XX:+PrintCompilation and prints the lines
// about this file's classes. Pass "all" to see every line.

interface KShape { fun area(): Double }
class KSquare(private val s: Double) : KShape { override fun area() = s * s }
class KCircle(private val r: Double) : KShape { override fun area() = Math.PI * r * r }
class KTri(private val b: Double, private val h: Double) : KShape { override fun area() = 0.5 * b * h }

fun total(shapes: Array<KShape>): Double {
    var sum = 0.0
    for (s in shapes) sum += s.area()        // one call site: first only squares, later three types
    return sum
}

fun longLoop(): Long {                       // called once, but the loop runs 50 million times: OSR
    var acc = 0L
    for (i in 0 until 50_000_000) acc += (i xor (i ushr 3))
    return acc
}

fun work() {
    println(longLoop())
    val squares = Array<KShape>(1000) { KSquare(it.toDouble()) }
    var r = 0.0
    repeat(20_000) { r += total(squares) }   // only KSquare seen so far
    val mixed = Array(999) {
        when (it % 3) { 0 -> KSquare(it.toDouble()); 1 -> KCircle(it.toDouble()); else -> KTri(it.toDouble(), it.toDouble()) }
    }
    repeat(20_000) { r += total(mixed) }     // two new types reach the same call site
    println(r)
}

fun main(args: Array<String>) {
    if (args.firstOrNull() == "child") { work(); return }
    val all = args.firstOrNull() == "all"
    // the same as: java -XX:+PrintCompilation -cp <classpath> workbench.performance.l01.HotKt child
    val java = ProcessHandle.current().info().command().orElse("java")
    val p = ProcessBuilder(java, "-XX:+PrintCompilation", "-cp", System.getProperty("java.class.path"),
        "workbench.performance.l01.HotKt", "child").redirectErrorStream(true).start()
    p.inputReader().useLines { lines ->
        lines.filter { all || it.contains("l01.HotKt") || it.contains("l01.K") || !it.contains("::") }
            .filterNot { it.startsWith("Picked up") }
            .forEach(::println)
    }
    p.waitFor()
}
