package workbench.container.l03.demo

import workbench.container.l03.Container
import workbench.container.l03.SettlementService
import workbench.container.l03.demo.app.CardIssuerClient
import workbench.container.l03.demo.app.DemoApp
import java.lang.ref.WeakReference
import java.nio.file.Files
import java.nio.file.Path

// Runs the reflective container, then looks inside this JVM with jcmd: a class histogram and a heap
// dump. Then it drops the container and checks what the garbage collector could take away.
// Run with -Pargs=wait to stop before each step and run jcmd yourself.
private object Here

private var container: Container? = null                          // the only reference to the container

fun main(args: Array<String>) {
    val wait = args.firstOrNull() == "wait"
    val pid = ProcessHandle.current().pid()
    val classes = Path.of(Here::class.java.protectionDomain.codeSource.location.toURI())
    val dump = Files.createDirectories(classes.parent.parent.parent.resolve("heapdumps")).resolve("container-kt.hprof")
    Files.deleteIfExists(dump)                                     // jcmd refuses to overwrite a dump

    container = Container(DemoApp.COMPONENTS)
    println("app: " + DemoApp.run(container!!))
    val generatedLoader = WeakReference(container!!.get(SettlementService::class.java).javaClass.classLoader)
    val proxyClass = container!!.get(CardIssuerClient::class.java).javaClass.name

    if (wait) {
        println("pid $pid. In a second terminal, from labs/:")
        println("  jcmd $pid GC.class_histogram | grep -E 'workbench|Proxy|ByteBuddy|ByteArray'")
        println("  jcmd $pid GC.heap_dump $dump")
        println("Then press Enter to drop the container.")
        System.`in`.read()
    } else {
        histogram(pid, proxyClass)
        jcmd(pid, "GC.heap_dump", dump.toString()).forEach { println("heap dump: $it") }
    }

    container = null
    repeat(10) {
        if (generatedLoader.get() != null) { System.gc(); Thread.sleep(50) }   // a request; repeat until it is gone
    }
    println("after dropping the container:")
    println("  Byte Buddy's class loader collected: ${generatedLoader.get() == null}")
    println("  $proxyClass still loaded: ${stillLoaded(proxyClass)}")
    if (wait) {
        println("Run the histogram again, then press Enter to exit.")
        System.`in`.read()
    } else {
        histogram(pid, proxyClass)
    }
}

/** The container's own lines of the histogram, then the proxy classes with live instances, grouped. */
private fun histogram(pid: Long, ourProxy: String) {
    val lines = jcmd(pid, "GC.class_histogram")
    println(lines[1])                                              // the column headings
    val ours = Regex(""".*(\.Container|SingletonCell|InterceptingHandler|SubclassBridge|\${'$'}ByteBuddy\${'$'}\w+|ByteArrayClassLoader|app\.PaymentService)( \(.*)?$""")
    lines.filter { ours.matches(it) || " $ourProxy " in it }.forEach(::println)
    val proxies = lines.map { it.trim().split(Regex("\\s+")) }.filter { it.size >= 4 && "\$Proxy" in it[3] }
    val instances = proxies.sumOf { it[1].toInt() }
    val mine = proxies.filter { it[3] == ourProxy }.sumOf { it[1].toInt() }
    val others = proxies.map { it[3] }.filter { it != ourProxy }
    val annotations = others.count(::isAnnotation)
    val byteBuddy = others.count { !isAnnotation(it) && it.startsWith("net.bytebuddy.") }
    println("  $instances proxy instances: $annotations annotation proxy classes, $byteBuddy in Byte Buddy's packages, " +
        "${others.size - annotations - byteBuddy} other, $mine of ours")
}

private fun isAnnotation(proxyClass: String): Boolean =
    runCatching { Annotation::class.java.isAssignableFrom(Class.forName(proxyClass, false, Here::class.java.classLoader)) }
        .getOrDefault(false)

private fun stillLoaded(name: String): Boolean =
    runCatching { Class.forName(name, false, Here::class.java.classLoader) }.isSuccess   // asks the loader, defines nothing

private fun jcmd(pid: Long, vararg command: String): List<String> {
    val cmd = listOf(Path.of(System.getProperty("java.home"), "bin", "jcmd").toString(), pid.toString()) + command
    val p = ProcessBuilder(cmd).redirectErrorStream(true).start()
    val out = p.inputReader().readLines().filterNot { it.startsWith("Picked up") }
    p.waitFor()
    return out
}
