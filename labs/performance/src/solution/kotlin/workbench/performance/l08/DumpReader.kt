package workbench.performance.l08

/**
 * Lesson 8 lab: read thread dumps the way you would at 3 a.m., but in code.
 *
 * Every method gets dumps already parsed by [ThreadDump.parse]. Look at [DumpedThread] for the fields.
 * The test fixtures are real `jcmd <pid> Thread.print -l` dumps of the FrozenService demo, taken 5 seconds apart.
 */
object DumpReader {

    /**
     * Hot threads: the threads whose CPU time grew from [before] to [after], biggest growth first, at most [n]
     * of them, each with its growth in milliseconds. Leave out threads whose CPU time did not grow at all.
     *
     * Match a thread in the two dumps by its nid, not by its name: names repeat (two pools can both
     * call their threads "worker"), but the OS thread id is unique while the thread lives.
     */
    fun hottest(before: ThreadDump, after: ThreadDump, n: Int): List<HotThread> =
        after.threads
            // 1. pair each thread with its earlier self, by OS thread id
            .mapNotNull { now -> before.byNid(now.nid)?.let { then -> HotThread(now.name, now.nid, now.cpuMs - then.cpuMs) } }
            // 2. a RUNNABLE thread that is waiting in a socket read has a growth of zero: drop it
            .filter { it.cpuMs > 0.0 }
            // 3. biggest growth first
            .sortedByDescending { it.cpuMs }
            .take(n)

    /**
     * Who is in the way: start at [threadName], then follow the lock it waits for to the thread that holds it,
     * then the lock that thread waits for, and so on.
     *
     * - Stop at a thread that waits for nothing, or for a lock nobody holds (an idle pool thread waits for a
     *   condition, which has no owner).
     * - If a name comes back, you found a deadlock: add that name once more and stop, so the list reads
     *   as a cycle, for example `[merge-A, merge-B, merge-A]`.
     * - Return an empty list when there is no thread called [threadName].
     */
    fun blockedChain(dump: ThreadDump, threadName: String): List<String> {
        var thread = dump.byName(threadName) ?: return emptyList()
        val chain = mutableListOf(thread.name)
        while (true) {
            // 1. what does it want, and who has it?
            val owner = thread.waitsFor?.let(dump::ownerOf) ?: return chain
            // 2. a name we have seen already closes a cycle: that is a deadlock
            val seen = owner.name in chain
            chain += owner.name
            if (seen) return chain
            // 3. keep walking from the owner
            thread = owner
        }
    }

    /**
     * Stuck threads: compare several dumps taken a few seconds apart and return, sorted by name, the threads that
     * - appear in every dump (match by nid),
     * - have exactly the same frames in every dump,
     * - have at least one frame that starts with [appPrefix] (your own code is in the stack, so it isn't an idle
     *   pool thread or a JVM thread), and
     * - used less than [cpuBudgetMs] of CPU between the first dump and the last (a thread that burns CPU in the
     *   same frame is hot, not stuck).
     */
    fun stuck(dumps: List<ThreadDump>, appPrefix: String, cpuBudgetMs: Double = 10.0): List<String> {
        if (dumps.isEmpty()) return emptyList()
        val first = dumps.first()
        val last = dumps.last()
        return first.threads
            // 1. your code is somewhere in the stack
            .filter { t -> t.frames.any { it.startsWith(appPrefix) } }
            // 2. the same thread, in the same frames, in every dump
            .filter { t -> dumps.all { d -> d.byNid(t.nid)?.frames == t.frames } }
            // 3. and it did not burn CPU while it sat there
            .filter { t -> last.byNid(t.nid)!!.cpuMs - t.cpuMs < cpuBudgetMs }
            .map { it.name }
            .sorted()
    }
}
