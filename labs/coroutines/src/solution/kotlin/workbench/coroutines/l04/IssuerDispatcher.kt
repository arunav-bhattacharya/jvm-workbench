package workbench.coroutines.l04

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers

// A view over IO: at most 20 at once, and IO views are elastic, so this budget is added on
// top of IO's own 64 rather than taken out of it. No pool to create or close.
fun issuerDispatcher(): CoroutineDispatcher = Dispatchers.IO.limitedParallelism(20, "issuer")
