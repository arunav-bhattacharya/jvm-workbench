package workbench.startup.l02

import java.util.concurrent.CopyOnWriteArrayList

/**
 * A class loader that defines every class whose name starts with [prefix] itself, from the
 * class files its parent can see, and records each name in the order it defined it.
 * Every other class (java.*, kotlin.*, the lab's own classes) goes to the parent as usual.
 */
class RecordingClassLoader(parent: ClassLoader, private val prefix: String) : ClassLoader(parent) {
    private val names = CopyOnWriteArrayList<String>()

    /** Names this loader has defined, in the order it defined them. */
    fun defined(): List<String> = names.toList()

    override fun loadClass(name: String, resolve: Boolean): Class<*> {
        // 1. not ours: normal parent-first delegation (and the JDK's classes stay shared)
        if (!name.startsWith(prefix)) return super.loadClass(name, resolve)

        // 2. ours: child-first, one definition per name even if two threads ask at once
        synchronized(getClassLoadingLock(name)) {
            val c = findLoadedClass(name) ?: run {
                val path = name.replace('.', '/') + ".class"
                val bytes = parent.getResourceAsStream(path)?.use { it.readBytes() }
                    ?: throw ClassNotFoundException(name)
                defineClass(name, bytes, 0, bytes.size).also { names += name }   // 3. record it
            }
            if (resolve) resolveClass(c)
            return c
        }
    }
}
