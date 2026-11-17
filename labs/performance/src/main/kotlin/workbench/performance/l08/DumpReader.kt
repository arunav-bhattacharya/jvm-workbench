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
    fun hottest(before: ThreadDump, after: ThreadDump, n: Int): List<HotThread> {
        throw UnsupportedOperationException("TODO: match threads by nid, compute the cpuMs growth, sort, take n")
    }

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
        throw UnsupportedOperationException("TODO: follow waitsFor -> ownerOf until it ends or repeats")
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
        throw UnsupportedOperationException("TODO: keep threads whose stacks never change and whose CPU stays flat")
    }
}
