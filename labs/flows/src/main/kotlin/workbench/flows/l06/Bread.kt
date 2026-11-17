package workbench.flows.l06

import kotlinx.coroutines.flow.Flow

/**
 * A [kind] of loaf from [bakery], with a [backup] bakery:
 *
 * 1. each call to the bakery gets 300 ms (timeout() on the bakery's flow),
 * 2. a transient failure (see isTransient) is retried with retryWithBackoff() and its defaults,
 * 3. when the bakery has given up on a transient failure, the loaf comes from [backup],
 * 4. a failure that isn't transient (a bread nobody bakes, a bug) reaches the caller unchanged,
 *    with no call to the backup,
 * 5. if the CALLER is cancelled, nothing is retried and the backup is never called.
 */
fun freshLoaf(kind: String, bakery: Bakery, backup: Bakery): Flow<Loaf> =
    TODO("timeout, then retryWithBackoff, then catch with the backup")

/**
 * The lines of the delivery [note], retried with retryWithBackoff() when reading fails mid-way.
 * A retry reads the note again from the top, so lines already delivered come again.
 * Every line id must reach the collector exactly once per collection of this flow.
 *
 * Bug: duplicates after a retry.
 */
fun eachLineOnce(note: Flow<NoteLine>): Flow<NoteLine> =
    note.retryWithBackoff()
