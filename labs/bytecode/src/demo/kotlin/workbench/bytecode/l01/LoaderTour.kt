package workbench.bytecode.l01

import java.lang.management.ManagementFactory

/** Which loader defined which class, and the chain a class-loading request walks up. */
fun main() {
    show(String::class.java)                  // java.lang.String, in java.base
    show(java.sql.Connection::class.java)     // java.sql, a platform module
    show(TourMarker::class.java)              // this program, on the class path
    show(Unit::class.java)                    // the Kotlin standard library jar, also on the class path

    val chain = generateSequence(TourMarker::class.java.classLoader) { it.parent }
        .joinToString("") { "${it.name} -> " }
    println("delegation chain: ${chain}bootstrap (null)")
    println("classes loaded so far: ${ManagementFactory.getClassLoadingMXBean().loadedClassCount}")
}

private class TourMarker

private fun show(c: Class<*>) {
    val l = c.classLoader
    println("%-34s loader=%-9s module=%s".format(c.name, l?.name ?: "bootstrap", c.module.name))
}
