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
    /**
     * TODO:
     * 1. One deadline for both checks: `val deadline = System.nanoTime() + budget.toNanos()`.
     * 2. Create `Executors.newVirtualThreadPerTaskExecutor()` and wrap it in an
     *    `ExecutorCompletionService<Boolean>`. Submit the safety check as
     *    `safetyBulkhead.call(deadline - System.nanoTime()) { safety.passes(t) }`, and the limits check as it is.
     * 3. Twice: `poll` the next finished check with the time left. `null` means the deadline passed:
     *    return [fallback]. Otherwise call `get()`. An `ExecutionException` whose cause is a
     *    `TimeoutException` (no permit in time) also means [fallback]. Any other failure, or `false`,
     *    means [Verdict.DECLINED]. If both pass, [Verdict.APPROVED].
     * 4. In a `finally`: `shutdownNow()` to interrupt whatever is still running, then `close()` to
     *    wait until those threads have ended.
     */
    fun screen(t: Transfer): Verdict {
        TODO("fan out both checks on virtual threads, fail fast, fall back at the deadline")
    }

    /** The small-amount rule: when the checks can't answer in time, small transfers go through and large ones are turned away. */
    private fun fallback(t: Transfer): Verdict =
        if (t.cents() <= smallAmountCents) Verdict.LET_THROUGH else Verdict.TIMED_OUT
}
