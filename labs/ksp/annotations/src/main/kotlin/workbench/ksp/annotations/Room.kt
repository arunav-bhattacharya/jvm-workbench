package workbench.ksp.annotations

/**
 * Lesson 3: which room a class's boxes go to, for example `@Room("kitchen")`. An annotation argument the
 * processor reads. RUNTIME retention so a reflection version can read it too.
 */
@Target(AnnotationTarget.CLASS)
@Retention(AnnotationRetention.RUNTIME)
annotation class Room(val name: String)
