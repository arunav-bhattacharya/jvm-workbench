package workbench.ksp.l07

import com.google.devtools.ksp.ApiFeatures
import com.google.devtools.ksp.buildApiFeatures
import com.google.devtools.ksp.processing.CodeGenerator
import com.google.devtools.ksp.processing.Dependencies
import com.google.devtools.ksp.processing.KSPLogger
import com.google.devtools.ksp.processing.Resolver
import com.google.devtools.ksp.processing.SymbolProcessor
import com.google.devtools.ksp.processing.SymbolProcessorEnvironment
import com.google.devtools.ksp.processing.SymbolProcessorProvider
import com.google.devtools.ksp.symbol.ClassKind
import com.google.devtools.ksp.symbol.KSAnnotated
import com.google.devtools.ksp.symbol.KSClassDeclaration
import com.squareup.kotlinpoet.ANY
import com.squareup.kotlinpoet.CodeBlock
import com.squareup.kotlinpoet.FileSpec
import com.squareup.kotlinpoet.FunSpec
import com.squareup.kotlinpoet.LIST
import com.squareup.kotlinpoet.MemberName
import com.squareup.kotlinpoet.ParameterizedTypeName.Companion.parameterizedBy
import com.squareup.kotlinpoet.PropertySpec
import com.squareup.kotlinpoet.STRING
import com.squareup.kotlinpoet.TypeSpec
import com.squareup.kotlinpoet.joinToCode
import com.squareup.kotlinpoet.ksp.toClassName
import com.squareup.kotlinpoet.ksp.writeTo
import workbench.ksp.annotations.Inventory

// Lesson 7: one inventory card per class (an isolating output, given) and one master list of every
// @Inventory class (an aggregating output, the exercise), named by a processor option.
//   ./gradlew :ksp:test --tests 'workbench.ksp.l07.*'
//   ./gradlew :ksp:app:compileL07Kotlin -Pksp.incremental.log=true      then read app/build/kspCaches/l07/logs/

/** The job sheet: `ksp { arg("movemate.listName", "MovingDayList") }`, or a line in app/src/l07/ksp.properties. */
const val LIST_NAME = "movemate.listName"

/** Optional: the package of the generated list. Without it the list goes to package `movemate`. */
const val LIST_PACKAGE = "movemate.listPackage"

/**
 * Given: a teaching switch that no real processor has, so the Try-it can show what each choice of Dependencies
 * does to an incremental build. Without it the list uses yours, [listDependencies]. The other values:
 * `isolating` (an aggregating output declared isolating), `none` (no source file named at all) and `all`
 * (Dependencies.ALL_FILES).
 */
const val LIST_DEPENDENCIES = "movemate.listDependencies"

/** What the processor needs from its options. */
data class ListOptions(val listName: String, val packageName: String)

/** KSP creates the processor through this provider. Registered in workbench/ksp/l07/SymbolProcessorProvider. */
class MasterListProcessorProvider : SymbolProcessorProvider {
    override fun create(environment: SymbolProcessorEnvironment): SymbolProcessor =
        MasterListProcessor(environment.codeGenerator, environment.logger, environment.options)
}

class MasterListProcessor(
    private val codeGenerator: CodeGenerator,
    private val logger: KSPLogger,
    private val options: Map<String, String>,
) : SymbolProcessor {

    // KSP 2.3.14's warning-free style: say which newer API behaviours this processor accepts.
    override val apiFeatures: ApiFeatures = buildApiFeatures {
        enableBackingFields = true
        enableContextParameters = true
    }

    private var listWritten = false

    // Given code: while the lab is unfinished this logs a warning and generates nothing,
    // so a real build with -Pmine=l07 still runs.
    override fun process(resolver: Resolver): List<KSAnnotated> = try {
        processList(resolver)
    } catch (e: NotImplementedError) {
        logger.warn("l07 not done yet: ${e.message?.substringAfter("not implemented: ")}")
        emptyList()
    }

    /**
     * Given: the five moves. Round 1 sees every source file that changed (and, through the aggregating list, every
     * file the list came from). Round 2 sees only the cards written in round 1, which carry no @Inventory, so the
     * list is written once.
     */
    fun processList(resolver: Resolver): List<KSAnnotated> {
        if (listWritten) return emptyList()
        // 2. Check the job sheet first: without a list name there is nothing to write
        val listOptions = readListOptions(options, logger) ?: return emptyList()
        // 1. Find
        val found = resolver.getSymbolsWithAnnotation(Inventory::class.qualifiedName!!).toList()
        // 2. Check each symbol
        val classes = found.filter { isPackable(it) }.map { it as KSClassDeclaration }
        if (classes.isEmpty()) return emptyList()
        // 3. Read and 4. Write: one card per class, rebuilt only when that class's own file changes (isolating)
        for (cls in classes) {
            inventoryCardFile(cls).writeTo(codeGenerator, Dependencies(aggregating = false, cls.containingFile!!))
        }
        // 4. Write: one master list for all of them (aggregating)
        val dependencies = when (options[LIST_DEPENDENCIES]) {
            "isolating" -> Dependencies(false, *classes.mapNotNull { it.containingFile }.distinct().toTypedArray())
            "all" -> Dependencies.ALL_FILES
            "none" -> Dependencies(false)
            else -> listDependencies(classes)
        }
        masterListFile(classes, listOptions).writeTo(codeGenerator, dependencies)
        listWritten = true
        return emptyList()
    }

    /** Given: only classes get cards. */
    private fun isPackable(symbol: KSAnnotated): Boolean {
        if (symbol is KSClassDeclaration && symbol.classKind == ClassKind.CLASS) return true
        val name = (symbol as? KSClassDeclaration)?.simpleName?.asString() ?: symbol.toString()
        val kind = (symbol as? KSClassDeclaration)?.classKind?.name?.lowercase()?.replace('_', ' ') ?: "not a class"
        logger.error("@Inventory goes on a class, but $name is ${if (kind.first() in "aeiou") "an" else "a"} $kind", symbol)
        return false
    }
}

/**
 * 2. Check: read the job sheet. [LIST_NAME] is required and must be a class name; [LIST_PACKAGE] is optional
 * (default `movemate`). Returns null after one logger.error that says what is wrong and how to fix it.
 */
fun readListOptions(options: Map<String, String>, logger: KSPLogger): ListOptions? {
    val listName = options[LIST_NAME]
    if (listName == null) {
        logger.error(
            "MasterListProcessor needs the processor option $LIST_NAME, the name of the list it generates. " +
                "Add ksp { arg(\"$LIST_NAME\", \"MovingDayList\") } to the build file.",
        )
        return null
    }
    if (!listName.matches(Regex("[A-Z][A-Za-z0-9]*"))) {
        logger.error("$LIST_NAME must be a class name such as MovingDayList, but it is '$listName'")
        return null
    }
    return ListOptions(listName, options[LIST_PACKAGE] ?: "movemate")
}

/**
 * 4. Write, part 1: the Dependencies of the master list. The list is aggregating (any new or changed file can
 * change it), and it came from the file of every class on it.
 */
fun listDependencies(classes: List<KSClassDeclaration>): Dependencies =
    Dependencies(aggregating = true, *classes.mapNotNull { it.containingFile }.distinct().toTypedArray())

/**
 * 4. Write, part 2: the master list, an object named by the option, with the classes sorted by simple name:
 * ```
 * public object MovingDayList {
 *   public val names: List<String> = listOf("Bookshelf", "Box", "Lamp", "Plant")
 *   public fun cardFor(thing: Any): String = when (thing) { is Bookshelf -> thing.inventoryCard() ... }
 * }
 * ```
 */
fun masterListFile(classes: List<KSClassDeclaration>, options: ListOptions): FileSpec {
    val sorted = classes.sortedBy { it.simpleName.asString() }
    val names = sorted.map { CodeBlock.of("%S", it.simpleName.asString()) }.joinToCode()
    val cardFor = FunSpec.builder("cardFor")
        .addParameter("thing", ANY)
        .returns(STRING)
        .beginControlFlow("return when (thing)")
    for (cls in sorted) {
        // %T imports the class, %M imports its card function if the list lives in another package
        cardFor.addStatement("is %T -> thing.%M()", cls.toClassName(), MemberName(cls.packageName.asString(), "inventoryCard"))
    }
    // a string template in plain quotes: %L writes it as it is (%P would choose triple quotes)
    cardFor.addStatement("else -> error(%L)", "\"${options.listName} has no card for \${thing::class.simpleName}\"")
        .endControlFlow()
    val list = TypeSpec.objectBuilder(options.listName)
        .addProperty(PropertySpec.builder("names", LIST.parameterizedBy(STRING)).initializer("listOf(%L)", names).build())
        .addFunction(cardFor.build())
        .build()
    return FileSpec.builder(options.packageName, options.listName)
        .addFileComment("Generated by MasterListProcessor from %L. Do not edit.", if (sorted.size == 1) "1 class" else "${sorted.size} classes")
        .addType(list)
        .build()
}

/**
 * Given (lesson 2's card, written with KotlinPoet): `fun Lamp.inventoryCard(): String` returning
 * `Lamp: name=desk lamp, bulbs=1, shade=null`, from the primary constructor's properties in order.
 */
fun inventoryCardFile(cls: KSClassDeclaration): FileSpec {
    val name = cls.simpleName.asString()
    val properties = cls.primaryConstructor?.parameters.orEmpty().filter { it.isVal || it.isVar }
        .map { it.name!!.asString() }
    val template = "$name: " + properties.joinToString(", ") { "$it=\${$it}" }
    return FileSpec.builder(cls.packageName.asString(), "${name}InventoryCard")
        .addFileComment("Generated by MasterListProcessor from %L. Do not edit.", name)
        .addFunction(
            FunSpec.builder("inventoryCard")
                .receiver(cls.toClassName())
                .returns(STRING)
                .addStatement("return %L", "\"$template\"") // the text holds only names, so plain quotes are safe
                .build(),
        )
        .build()
}
