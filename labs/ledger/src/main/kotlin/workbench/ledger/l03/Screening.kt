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

    /** The deadline passed, and the amount is small enough to accept without the checks (stand-in). */
    STAND_IN,

    /** A check said no, or failed. */
    DECLINED,

    /** The deadline passed, and the amount is too large to accept without the checks. */
    TIMED_OUT,
}

/**
 * Screens one transfer. The fraud check (slow, behind [fraudBulkhead]) and the limits check (fast)
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
    private val fraud: Check,
    private val limits: Check,
    private val fraudBulkhead: Bulkhead,
    private val budget: Duration,
    private val standInLimitCents: Long,
) {
    /**
     * TODO:
     * 1. One deadline for both checks: `val deadline = System.nanoTime() + budget.toNanos()`.
     * 2. Create `Executors.newVirtualThreadPerTaskExecutor()` and wrap it in an
     *    `ExecutorCompletionService<Boolean>`. Submit the fraud check as
     *    `fraudBulkhead.call(deadline - System.nanoTime()) { fraud.passes(t) }`, and the limits check as it is.
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

    /** The stand-in rule: when the checks can't answer in time, small transfers go through and large ones are turned away. */
    private fun fallback(t: Transfer): Verdict =
        if (t.cents() <= standInLimitCents) Verdict.STAND_IN else Verdict.TIMED_OUT
}
