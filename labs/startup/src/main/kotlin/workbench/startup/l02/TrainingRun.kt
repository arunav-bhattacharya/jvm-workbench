package workbench.startup.l02

/**
 * A miniature of what `-XX:DumpLoadedClassList` and an AOT-cache training run do: run a
 * workload once and write down which classes it needed. Whatever the workload never touched
 * is not in the list, so it would not be in the archive either.
 */
object TrainingRun {

    /**
     * Creates a fresh [RecordingClassLoader] for [prefix] (with [parent] as its parent),
     * initializes [entryClass] through it, and calls its public static `handle(String)` method
     * once for each of [requests], in order. Returns the class list: [RecordingClassLoader.defined].
     *
     * TODO: use `Class.forName(entryClass, true, loader)` and `getMethod("handle", String::class.java)`.
     */
    fun classList(parent: ClassLoader, prefix: String, entryClass: String, requests: List<String>): List<String> =
        TODO("run the workload in a fresh RecordingClassLoader and return what it defined")

    /**
     * The classes that [production] needed and [training] never loaded. In a real archive,
     * these would be loaded, parsed and verified the slow way on every start.
     *
     * TODO: one line with set operations.
     */
    fun missing(training: List<String>, production: List<String>): Set<String> =
        TODO("classes in production but not in training")
}
