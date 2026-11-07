package workbench.startup.l02

/**
 * A miniature of what `-XX:DumpLoadedClassList` and an AOT-cache training run do: run a
 * workload once and write down which classes it needed.
 */
object TrainingRun {

    fun classList(parent: ClassLoader, prefix: String, entryClass: String, requests: List<String>): List<String> {
        val loader = RecordingClassLoader(parent, prefix)          // 1. fresh: nothing defined yet
        val handle = Class.forName(entryClass, true, loader)
            .getMethod("handle", String::class.java)
        requests.forEach { handle.invoke(null, it) }               // 2. the training workload
        return loader.defined()                                    // 3. the class list
    }

    // production minus training: what a cache trained on this workload would not contain
    fun missing(training: List<String>, production: List<String>): Set<String> =
        production.toSet() - training.toSet()
}
