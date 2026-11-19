package workbench.injector.annotations

/**
 * Marks an `object` whose `@Provides` functions tell the plan how to get things it can't build from an
 * `@Inject` constructor, such as a class from a library you can't put a note on.
 */
@Target(AnnotationTarget.CLASS)
@Retention(AnnotationRetention.RUNTIME)
@MustBeDocumented
annotation class Module
