package workbench.injector.annotations

/**
 * One for the whole day: the plan builds this class (or calls this `@Provides` function) once per component
 * and hands the same object to everyone who asks. Without it, every request gets a new one, like a fresh roll
 * of tape for each room.
 */
@Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.RUNTIME)
@MustBeDocumented
annotation class Singleton
