package workbench.nio.l06

import io.vertx.core.Future
import io.vertx.core.Vertx
import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.Timeout
import java.util.concurrent.ExecutionException
import java.util.concurrent.TimeUnit

@Timeout(20)
class DispatcherTest {
    private lateinit var vertx: Vertx

    @BeforeEach
    fun start() {
        vertx = Vertx.vertx()
    }

    @AfterEach
    fun stop() {
        vertx.close().toCompletionStage().toCompletableFuture().get(10, TimeUnit.SECONDS)
    }

    private fun <T> Future<T>.awaitResult(): T = toCompletionStage().toCompletableFuture().get(10, TimeUnit.SECONDS)

    private fun target(returns: ReturnKind, vararg markers: Marker) =
        DispatchRules.target(Endpoint("e", returns, markers.toSet()))

    @Test
    fun `the return type picks the thread`() {
        assertThat(target(ReturnKind.PLAIN)).isEqualTo(Target.WORKER)
        for (kind in listOf(ReturnKind.UNI, ReturnKind.MULTI, ReturnKind.COMPLETION_STAGE, ReturnKind.PUBLISHER, ReturnKind.SUSPEND)) {
            assertThat(target(kind)).`as`(kind.name).isEqualTo(Target.IO_THREAD)
        }
    }

    @Test
    fun `@Blocking and @NonBlocking override the return type`() {
        assertThat(target(ReturnKind.UNI, Marker.BLOCKING)).isEqualTo(Target.WORKER)
        assertThat(target(ReturnKind.PLAIN, Marker.NON_BLOCKING)).isEqualTo(Target.IO_THREAD)
    }

    @Test
    fun `@Transactional makes a Uni endpoint blocking in 3_40, unless an explicit annotation says otherwise`() {
        assertThat(target(ReturnKind.UNI, Marker.TRANSACTIONAL)).isEqualTo(Target.WORKER)
        assertThat(target(ReturnKind.UNI, Marker.TRANSACTIONAL, Marker.NON_BLOCKING)).isEqualTo(Target.IO_THREAD)
    }

    @Test
    fun `@RunOnVirtualThread runs on a virtual thread`() {
        assertThat(target(ReturnKind.PLAIN, Marker.RUN_ON_VIRTUAL_THREAD)).isEqualTo(Target.VIRTUAL_THREAD)
    }

    @Test
    fun `invoke runs each body on the thread its endpoint asks for`() {
        val dispatcher = Dispatcher(vertx)
        val io = dispatcher.invoke(Endpoint("reactive", ReturnKind.UNI)) { Thread.currentThread().name }.awaitResult()
        val worker = dispatcher.invoke(Endpoint("blocking", ReturnKind.PLAIN)) { Thread.currentThread().name }.awaitResult()
        val virtual = dispatcher.invoke(Endpoint("vt", ReturnKind.PLAIN, setOf(Marker.RUN_ON_VIRTUAL_THREAD))) {
            Thread.currentThread().isVirtual
        }.awaitResult()
        assertThat(io).startsWith("vert.x-eventloop-thread-")
        assertThat(worker).startsWith("vert.x-worker-thread-")
        assertThat(virtual).isTrue()
    }

    @Test
    fun `blocking on the IO thread fails fast, and the same body works on a worker`() {
        val dispatcher = Dispatcher(vertx)
        val body = { BlockingGuard.check("a JDBC query"); "ok" }
        assertThatThrownBy { dispatcher.invoke(Endpoint("reactive", ReturnKind.UNI), body).awaitResult() }
            .isInstanceOf(ExecutionException::class.java)
            .cause()
            .isInstanceOf(BlockingNotAllowedException::class.java)
            .hasMessage("Attempting a JDBC query on an IO thread")
        assertThat(dispatcher.invoke(Endpoint("blocking", ReturnKind.PLAIN), body).awaitResult()).isEqualTo("ok")
        assertThat(dispatcher.invoke(Endpoint("vt", ReturnKind.UNI, setOf(Marker.RUN_ON_VIRTUAL_THREAD)), body).awaitResult()).isEqualTo("ok")
    }

    @Test
    fun `four blocking endpoints overlap on the worker pool`() {
        val dispatcher = Dispatcher(vertx)
        val t0 = System.nanoTime()
        val calls = List(4) { i -> dispatcher.invoke(Endpoint("balance-$i", ReturnKind.PLAIN)) { Thread.sleep(300); i } }
        Future.all(calls).awaitResult()
        val ms = (System.nanoTime() - t0) / 1_000_000
        assertThat(ms).`as`("4 x 300 ms on the worker pool, total ms").isLessThan(900)
    }
}
