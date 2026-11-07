package workbench.startup.l02

/**
 * A class loader that defines every class whose name starts with [prefix] itself, from the
 * class files its parent can see, and records each name in the order it defined it.
 * Every other class (java.*, kotlin.*, the lab's own classes) goes to the parent as usual.
 *
 * This "child-first for one package" shape is what plugin systems and app servers use. Leyden's
 * AOT cache does not support classes from custom class loaders yet, which is why Quarkus has a
 * separate aot-jar packaging that leaves all class loading to the JDK's own loaders.
 *
 * TODO:
 * - `loadClass`: for a name outside [prefix], call `super.loadClass(name, resolve)`.
 *   For a name inside it, inside `synchronized(getClassLoadingLock(name))`:
 *   return `findLoadedClass(name)` if it is already defined; otherwise read the bytes of
 *   `name.replace('.', '/') + ".class"` with `parent.getResourceAsStream(...)`, call
 *   `defineClass`, record the name, and `resolveClass` it if [resolve] is true.
 *   A missing class file must throw `ClassNotFoundException(name)`.
 * - `defined`: a copy of the recorded names, in definition order.
 */
class RecordingClassLoader(parent: ClassLoader, private val prefix: String) : ClassLoader(parent) {

    /** Names this loader has defined, in the order it defined them. */
    fun defined(): List<String> = TODO("return a copy of the recorded names")

    override fun loadClass(name: String, resolve: Boolean): Class<*> {
        TODO("child-first for names that start with prefix, parent-first for the rest")
    }
}
