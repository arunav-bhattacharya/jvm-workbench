package workbench.container.l01.demo

import workbench.container.l01.Component
import java.lang.management.ManagementFactory
import java.net.URLClassLoader
import java.nio.file.Files
import java.nio.file.Path
import java.util.jar.JarEntry
import java.util.jar.JarOutputStream
import kotlin.io.path.name

// Scans one package for @Component classes, first in a directory, then in two JAR files.
private const val PACKAGE = "workbench.container.l01.demo.app"
private const val INITIALIZE = false            // try true: what does Class.forName(name, true, loader) run?

private object Here

fun main() {
    val loader = Here::class.java.classLoader
    val path = PACKAGE.replace('.', '/')
    val before = ManagementFactory.getClassLoadingMXBean().totalLoadedClassCount
    for (root in loader.getResources(path).toList()) {               // one URL per class path entry
        println("root: ..." + root.toString().substringAfter("/build").let { "/build$it" })
        val components = Files.list(Path.of(root.toURI())).use { files ->
            files.sorted().toList()
                .filter { it.name.endsWith(".class") }
                .map { Class.forName("$PACKAGE.${it.name.removeSuffix(".class")}", INITIALIZE, loader) }
                .filter { it.isAnnotationPresent(Component::class.java) }
                .map { it.simpleName }
        }
        println("components: $components")
    }
    val after = ManagementFactory.getClassLoadingMXBean().totalLoadedClassCount
    println("classes loaded during the scan: ${after - before}")

    // The same package packed into a JAR twice: with directory entries, and with files only.
    val packageDir = Path.of(loader.getResource(path)!!.toURI())
    val appClasses = path.split("/").fold(packageDir) { dir, _ -> dir.parent }                  // build/classes/java/demo
    val dir = Files.createDirectories(appClasses.parent.parent.parent.resolve("cap4"))       // container/build/cap4
    for (withDirectories in listOf(true, false)) {
        val jar = pack(appClasses, path, dir.resolve(if (withDirectories) "kt-app-with-dirs.jar" else "kt-app-files-only.jar"), withDirectories)
        URLClassLoader(arrayOf(jar.toUri().toURL()), null).use { jarLoader ->
            val roots = jarLoader.getResources(path).toList()
            println("%-21s getResources found %d root(s) %s".format(jar.name, roots.size,
                if (roots.isEmpty()) "" else "${roots[0].protocol}:...!/$path"))
        }
    }
}

private fun pack(classes: Path, path: String, jar: Path, withDirectories: Boolean): Path {
    JarOutputStream(Files.newOutputStream(jar)).use { out ->
        if (withDirectories) {                     // "workbench/", "workbench/container/", ... as entries of their own
            var prefix = ""
            for (part in path.split("/")) {
                prefix += "$part/"
                out.putNextEntry(JarEntry(prefix))
                out.closeEntry()
            }
        }
        Files.list(classes.resolve(path)).use { files ->
            for (f in files.sorted().toList()) {
                out.putNextEntry(JarEntry("$path/${f.name}"))
                out.write(Files.readAllBytes(f))
                out.closeEntry()
            }
        }
    }
    return jar
}
