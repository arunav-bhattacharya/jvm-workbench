package workbench.container.l03

import kotlin.reflect.KClass

/** Record how long every call of this method takes, in the container's [CallLog]. */
@Retention(AnnotationRetention.RUNTIME)
@Target(AnnotationTarget.FUNCTION)
annotation class Timed

/** Call this method again, up to [attempts] calls in all, when it throws one of [on]. */
@Retention(AnnotationRetention.RUNTIME)
@Target(AnnotationTarget.FUNCTION)
annotation class Retry(val attempts: Int = 3, val on: Array<KClass<out Throwable>> = [RuntimeException::class])
