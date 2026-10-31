package workbench.coroutines.l04

import kotlinx.coroutines.CoroutineDispatcher

/**
 * The card issuer's client is blocking, and its connection pool has 20 connections.
 *
 * Return a dispatcher, named "issuer", that runs at most 20 blocking issuer calls at the
 * same time, and does allow 20. Do not create a new thread pool.
 */
fun issuerDispatcher(): CoroutineDispatcher {
    TODO("a view over Dispatchers.IO")
}
