package workbench.bytecode.l01

class KCounter {
    fun hit(): Int = ++hits

    companion object {
        @JvmField var hits = 0
    }
}

/** Defines KCounter itself (child-first); asks the parent for everything else. */
private class KChildFirst(name: String) : ClassLoader(name, KCounter::class.java.classLoader) {
    override fun loadClass(name: String, resolve: Boolean): Class<*> {
        if (name != KCounter::class.java.name) return super.loadClass(name, resolve)
        synchronized(getClassLoadingLock(name)) {
            findLoadedClass(name)?.let { return it }
            val bytes = parent.getResourceAsStream(name.replace('.', '/') + ".class")!!.use { it.readAllBytes() }
            return defineClass(name, bytes, 0, bytes.size)
        }
    }
}

/** The same class file defined by two loaders: two classes, two sets of statics. */
fun main() {
    val name = KCounter::class.java.name
    val c1 = KChildFirst("plugin-1").loadClass(name)
    val c2 = KChildFirst("plugin-2").loadClass(name)
    println("same name: ${c1.name == c2.name}")
    println("c1 == c2: ${c1 == c2}, c1 == KCounter::class.java: ${c1 == KCounter::class.java}")

    val fromPlugin1 = c1.getDeclaredConstructor().newInstance()
    repeat(2) { c1.getMethod("hit").invoke(fromPlugin1) }
    println("hits: plugin-1=${c1.getField("hits").get(null)}, plugin-2=${c2.getField("hits").get(null)}, app=${KCounter.hits}")

    try {
        val c = fromPlugin1 as KCounter   // checkcast against the app loader's KCounter
    } catch (e: ClassCastException) {
        println(e.message)
    }
}
