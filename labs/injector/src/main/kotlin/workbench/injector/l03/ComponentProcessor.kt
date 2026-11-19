package workbench.injector.l03

import com.google.devtools.ksp.ApiFeatures
import com.google.devtools.ksp.buildApiFeatures
import com.google.devtools.ksp.isPrivate
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
import com.google.devtools.ksp.symbol.KSFunctionDeclaration
import com.google.devtools.ksp.validate
import com.squareup.kotlinpoet.ClassName
import com.squareup.kotlinpoet.CodeBlock
import com.squareup.kotlinpoet.FileSpec
import com.squareup.kotlinpoet.FunSpec
import com.squareup.kotlinpoet.KModifier
import com.squareup.kotlinpoet.PropertySpec
import com.squareup.kotlinpoet.ParameterizedTypeName.Companion.parameterizedBy
import com.squareup.kotlinpoet.TypeSpec
import com.squareup.kotlinpoet.joinToCode
import com.squareup.kotlinpoet.ksp.toClassName
import com.squareup.kotlinpoet.ksp.writeTo

// Given code: lesson 2's component processor; what changed is the Write move, for Lazy and () -> T requests.

/** Registered in workbench/injector/l03/SymbolProcessorProvider, with the factory processor. */
class ComponentProcessorProvider : SymbolProcessorProvider {
    override fun create(environment: SymbolProcessorEnvironment): SymbolProcessor =
        ComponentProcessor(environment.codeGenerator, environment.logger)
}

/** For each @Component interface, `Generated<Name>`, written only when the whole plan checks out. */
class ComponentProcessor(
    private val codeGenerator: CodeGenerator,
    private val logger: KSPLogger,
) : SymbolProcessor {

    override val apiFeatures: ApiFeatures = buildApiFeatures {
        enableBackingFields = true
        enableContextParameters = true
    }

    // while the lab is unfinished this logs a warning and generates nothing
    override fun process(resolver: Resolver): List<KSAnnotated> = try {
        writeComponents(resolver)
    } catch (e: NotImplementedError) {
        logger.warn("l03 not done yet: ${e.message?.substringAfter("not implemented: ")}")
        emptyList()
    }

    fun writeComponents(resolver: Resolver): List<KSAnnotated> {
        // 1. Find: the components, and every @Module in this build (each one may add bindings to the plan)
        val (ready, later) = resolver.getSymbolsWithAnnotation(COMPONENT).toList()
            .partition { it.validate(apiFeatures = apiFeatures) }
        if (ready.isEmpty()) return later                     // a later round with no new component: nothing to plan
        val modules = resolver.getSymbolsWithAnnotation(MODULE).filterIsInstance<KSClassDeclaration>().toList()
        var moduleProblems = checkStrayProvides(resolver)
        val provided = modules.flatMap { checkedModule(it) ?: emptyList<ProvidesBinding>().also { moduleProblems = true } }

        // 2. Check: two bindings for one key are a problem of the modules, so check them once
        val graph = Graph(logger, provided)
        graph.checkDuplicates()
        val duplicates = graph.errors > 0

        for (component in ready.filterIsInstance<KSClassDeclaration>()) {
            val entryPoints = checkedEntryPoints(component) ?: continue
            // 2. Check and 3. Read: walk this component's graph, every problem in one pass
            val before = graph.errors
            val order = graph.creationOrder(entryPoints)
            if (graph.errors > before || duplicates || moduleProblems) continue
            // 4. Write: aggregating, from the component's file and every module's file
            val sources = (listOf(component) + modules).mapNotNull { it.containingFile }.distinct()
            componentFile(component, entryPoints, order, graph)
                .writeTo(codeGenerator, Dependencies(aggregating = true, *sources.toTypedArray()))
        }
        return later
    }

    /** A @Module must be an object (the component calls its functions without building it). */
    fun checkedModule(module: KSClassDeclaration): List<ProvidesBinding>? {
        val name = module.simpleName.asString()
        if (module.classKind != ClassKind.OBJECT) {
            logger.error("@Module goes on an object, so the component can call its functions, but $name is not an object", module)
            return null
        }
        val functions = module.getAllFunctions().filter { it.hasAnnotation(PROVIDES) }.toList()
        val hidden = functions.filter { it.isPrivate() }
        for (f in hidden) logger.error("$name.${f.simpleName.asString()}() is private, so the component can't call it", f)
        return functions.map { ProvidesBinding(module, it) }.takeIf { hidden.isEmpty() }
    }

    /** A @Provides function outside a @Module is never read: say so instead of ignoring it. Returns true on a problem. */
    fun checkStrayProvides(resolver: Resolver): Boolean {
        val stray = resolver.getSymbolsWithAnnotation(PROVIDES).filterIsInstance<KSFunctionDeclaration>()
            .filter { (it.parentDeclaration as? KSClassDeclaration)?.hasAnnotation(MODULE) != true }.toList()
        for (f in stray) logger.error("@Provides only works inside a @Module object, and ${f.simpleName.asString()}() is not in one", f)
        return stray.isNotEmpty()
    }

    /** The component's entry points (abstract functions without parameters), or null after an error. */
    fun checkedEntryPoints(component: KSClassDeclaration): List<EntryPoint>? {
        val name = component.simpleName.asString()
        if (component.classKind != ClassKind.INTERFACE) {
            logger.error("@Component goes on an interface that lists what the app asks for, but $name is not an interface", component)
            return null
        }
        val functions = component.getAllFunctions().filter { it.isAbstract }.toList()
        val withParameters = functions.filter { it.parameters.isNotEmpty() }
        for (e in withParameters) {
            logger.error("$name.${e.simpleName.asString()}() takes parameters, but a component function only names what it hands out", e)
        }
        return functions.map(::EntryPoint).takeIf { withParameters.isEmpty() }
    }
}

/** `truck`, `highwayRoute`, `gpsUnit` for a singleton (a val); `newTapeRoll` for the rest (a function). */
fun memberName(binding: Binding): String {
    val qualifier = binding.key.qualifier?.split(' ', '-', '_')?.filter(String::isNotEmpty)
        ?.joinToString("") { it.replaceFirstChar(Char::uppercase) }.orEmpty()
    val base = (qualifier + binding.className.simpleName).replaceFirstChar(Char::lowercase)
    return if (binding.singleton) base else "new" + base.replaceFirstChar(Char::uppercase)
}

/**
 * The singletons somebody asks for lazily or through a provider. Each one is held in a `Lazy` instead of being
 * built when the component is: `private val gpsUnit: Lazy<GpsUnit> = lazy { GpsUnitFactory.create() }`.
 */
fun heldLazily(order: List<Binding>): Set<Key> =
    order.flatMap { it.dependencies }.filter { it.kind != Kind.DIRECT }.map { it.key }.toSet()

/**
 * 4. Write: the expression that answers one request for [binding], asked for as [kind]. [held] is
 * [heldLazily]. For `gpsUnit` (a singleton held in a Lazy), `truck` (a singleton built at once) and
 * `newTapeRoll` (no @Singleton):
 *
 *     kind       gpsUnit               truck             newTapeRoll
 *     DIRECT     gpsUnit.value         truck             newTapeRoll()
 *     LAZY       gpsUnit               lazyOf(truck)     lazy { newTapeRoll() }
 *     PROVIDER   { gpsUnit.value }     { truck }         { newTapeRoll() }
 *
 * Use %N for the member name (from [memberName]).
 */
fun reference(binding: Binding, kind: Kind, held: Set<Key>): CodeBlock {
    TODO("write the expression for each kind of request: gpsUnit.value, gpsUnit, lazy { newTapeRoll() }, { newTapeRoll() } and the rest of the table")
}

/** `TruckFactory.create(driver, gpsUnit)` or `RouteModule.highway()`, with a [reference] for each dependency. */
fun construct(binding: Binding, graph: Graph, held: Set<Key>): CodeBlock {
    val arguments = binding.dependencies
        .map { reference(graph.bindingFor(it.key, it.type)!!, it.kind, held) }.joinToCode(", ")
    return when (binding) {
        is ConstructorBinding -> CodeBlock.of("%T.create(%L)", factoryName(binding), arguments)
        is ProvidesBinding -> CodeBlock.of("%T.%N(%L)", binding.module.toClassName(), binding.function.simpleName.asString(), arguments)
    }
}

/** `Generated<Interface>.kt`: a val per singleton in creation order (a Lazy for those asked lazily), a `new...()` function for the rest, the overrides. */
fun componentFile(component: KSClassDeclaration, entryPoints: List<EntryPoint>, order: List<Binding>, graph: Graph): FileSpec {
    val contract = component.toClassName()
    val generated = ClassName(contract.packageName, "Generated${contract.simpleName}")
    val type = TypeSpec.classBuilder(generated).addSuperinterface(contract)
    val held = heldLazily(order)
    for (binding in order) {
        val build = construct(binding, graph, held)
        when {
            binding.singleton && binding.key in held -> type.addProperty(
                PropertySpec.builder(memberName(binding), LAZY.parameterizedBy(binding.className), KModifier.PRIVATE)
                    .initializer("lazy { %L }", build).build(),
            )
            binding.singleton -> type.addProperty(
                PropertySpec.builder(memberName(binding), binding.className, KModifier.PRIVATE).initializer(build).build(),
            )
            else -> type.addFunction(
                FunSpec.builder(memberName(binding)).addModifiers(KModifier.PRIVATE).returns(binding.className)
                    .addStatement("return %L", build).build(),
            )
        }
    }
    for (entry in entryPoints) {
        val binding = graph.bindingFor(entry.key, entry.type)!!
        type.addFunction(
            FunSpec.builder(entry.function.simpleName.asString()).addModifiers(KModifier.OVERRIDE)
                .returns(binding.className).addStatement("return %L", reference(binding, Kind.DIRECT, held)).build(),
        )
    }
    return FileSpec.builder(generated)
        .addFileComment("Generated by ComponentProcessor from %L. Do not edit.", contract.simpleName)
        .addType(type.build())
        .build()
}

private val LAZY = ClassName("kotlin", "Lazy")
