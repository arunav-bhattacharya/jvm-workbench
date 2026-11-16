package workbench.ledger.l03

import java.time.Duration
import java.util.concurrent.ExecutionException
import java.util.concurrent.ExecutorCompletionService
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException

/** One remote check on a transfer: true lets it through, false denies it. It may also throw, block, or never answer. */
fun interface Check {
    fun passes(t: Transfer): Boolean
}

/** What screening decided about one transfer. */
enum class Verdict {
    /** Both checks passed in time. */
    APPROVED,

    /** The deadline passed, and the amount is small enough to let through without the checks. */
    LET_THROUGH,

    /** A check said no, or failed. */
    DECLINED,

    /** The deadline passed, and the amount is too large to accept without the checks. */
    TIMED_OUT,
}

/**
 * Screens one transfer. The safety check (slow, behind [safetyBulkhead]) and the limits check (fast)
 * run at the same time, each on its own virtual thread, inside one deadline of [budget].
 *
 * Rules the tests check:
 * - Both checks pass in time: [Verdict.APPROVED].
 * - The first check that says no, or throws, decides at once: [Verdict.DECLINED], and the other
 *   check is interrupted. This is fail-fast.
 * - The deadline passes first, or no bulkhead permit comes in time: [fallback]. Both checks are interrupted.
 * - When [screen] returns, no thread it started is still running.
 */
class Screening(
    private val safety: Check,
    private val limits: Check,
    private val safetyBulkhead: Bulkhead,
    private val budget: Duration,
    private val smallAmountCents: Long,
) {
    fun screen(t: Transfer): Verdict {
        val deadline = System.nanoTime() + budget.toNanos()                 // 1. one deadline for both checks
        val perTask = Executors.newVirtualThreadPerTaskExecutor()
        try {
            val done = ExecutorCompletionService<Boolean>(perTask)
            done.submit { safetyBulkhead.call(deadline - System.nanoTime()) { safety.passes(t) } }   // 2. fork both
            done.submit { limits.passes(t) }
            repeat(2) {
                val next = done.poll(deadline - System.nanoTime(), TimeUnit.NANOSECONDS)
                    ?: return fallback(t)                                    // 3. deadline passed: small-amount rule
                val passed = try {
                    next.get()
                } catch (e: ExecutionException) {
                    if (e.cause is TimeoutException) return fallback(t)      //    no safety permit in time
                    return Verdict.DECLINED                                  // 4. a check failed: fail fast
                }
                if (!passed) return Verdict.DECLINED                         // 4. a check said no: fail fast
            }
            return Verdict.APPROVED
        } finally {
            perTask.shutdownNow()                                            // 5. interrupt whatever still runs...
            perTask.close()                                                  //    ...and wait until those threads end
        }
    }

    /** The small-amount rule: when the checks can't answer in time, small transfers go through and large ones are turned away. */
    private fun fallback(t: Transfer): Verdict =
        if (t.cents() <= smallAmountCents) Verdict.LET_THROUGH else Verdict.TIMED_OUT
}
