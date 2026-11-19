package workbench.injector.annotations

/**
 * Inside a `@Module` object: "to get one of my return type, call me". The function's parameters are its own
 * dependencies, and the plan hands them in like constructor parameters.
 */
@Target(AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.RUNTIME)
@MustBeDocumented
annotation class Provides
