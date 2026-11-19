package workbench.injector.l02.demo;

import java.net.URI;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import javax.annotation.processing.AbstractProcessor;
import javax.annotation.processing.RoundEnvironment;
import javax.annotation.processing.SupportedAnnotationTypes;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.Element;
import javax.lang.model.element.ExecutableElement;
import javax.lang.model.element.TypeElement;
import javax.lang.model.element.VariableElement;
import javax.lang.model.type.TypeMirror;
import javax.lang.model.util.ElementFilter;
import javax.tools.Diagnostic;
import javax.tools.DiagnosticCollector;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.SimpleJavaFileObject;
import javax.tools.ToolProvider;
import workbench.injector.annotations.Component;
import workbench.injector.annotations.Inject;

// The closest Java equivalent: a javac annotation processor that walks each @Component's graph and reports a
// missing binding or a cycle with its path, on the exact parameter, through the Messager. (It does the first
// two checks only; the duplicates need modules.) main() runs javac in memory on two broken Java plans.
//   ./gradlew :injector:demo -Pmain=workbench.injector.l02.demo.CompileTimeMistakesDemoJava
public class CompileTimeMistakesDemoJava {

    @SupportedAnnotationTypes("workbench.injector.annotations.Component")
    public static class GraphCheckProcessor extends AbstractProcessor {

        @Override
        public SourceVersion getSupportedSourceVersion() {
            return SourceVersion.latestSupported();
        }

        @Override
        public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment round) {
            for (Element component : round.getElementsAnnotatedWith(Component.class)) {             // 1. Find
                for (ExecutableElement entry : ElementFilter.methodsIn(component.getEnclosedElements())) {
                    walk(entry.getReturnType(), new ArrayList<>(), new HashSet<>(), entry);
                }
            }
            return true;
        }

        /** Depth first, with the path the walk is on: the same walk as the KSP processor's creationOrder. */
        private void walk(TypeMirror type, List<String> path, Set<String> done, Element askedBy) {
            TypeElement cls = (TypeElement) processingEnv.getTypeUtils().asElement(type);
            String name = cls.getSimpleName().toString();
            if (done.contains(name)) return;
            if (path.contains(name)) {                                                               // 2. Check
                List<String> loop = new ArrayList<>(path.subList(path.indexOf(name), path.size()));
                loop.add(name);
                error("Dependency cycle: " + String.join(" needs ", loop), askedBy);
                return;
            }
            ExecutableElement constructor = ElementFilter.constructorsIn(cls.getEnclosedElements()).stream()
                    .filter(c -> c.getAnnotation(Inject.class) != null).findFirst().orElse(null);
            if (constructor == null) {
                List<String> needs = new ArrayList<>(path);
                needs.add(name);
                error(String.join(" needs ", needs) + ": nobody provides " + name, askedBy);
                return;
            }
            path.add(name);
            for (VariableElement p : constructor.getParameters()) walk(p.asType(), path, done, p);    // 3. Read
            path.remove(path.size() - 1);
            done.add(name);
        }

        private void error(String message, Element element) {
            processingEnv.getMessager().printMessage(Diagnostic.Kind.ERROR, message, element);
        }
    }

    public static void main(String[] args) {
        List<JavaFileObject> sources = List.of(
                source("movemate/missing/Missing.java", """
                        package movemate.missing;

                        import workbench.injector.annotations.*;

                        class Route { @Inject Route() {} }
                        class Driver { Driver(Route route) {} }                       // forgot @Inject
                        class Truck { @Inject Truck(Driver driver) {} }
                        class Crew { @Inject Crew(Truck truck) {} }
                        class MovingDay { @Inject MovingDay(Crew crew) {} }

                        @Component interface MissingPlan { MovingDay movingDay(); }
                        """),
                source("movemate/cycle/Cycle.java", """
                        package movemate.cycle;

                        import workbench.injector.annotations.*;

                        class Route { @Inject Route() {} }
                        class Driver { @Inject Driver(Route route, Truck truck) {} }  // waits for the truck
                        class Truck { @Inject Truck(Driver driver) {} }               // which waits for the driver
                        class Crew { @Inject Crew(Truck truck) {} }
                        class MovingDay { @Inject MovingDay(Crew crew) {} }

                        @Component interface CyclePlan { MovingDay movingDay(); }
                        """));
        JavaCompiler javac = ToolProvider.getSystemJavaCompiler();
        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
        JavaCompiler.CompilationTask task = javac.getTask(null, null, diagnostics,
                List.of("-classpath", System.getProperty("java.class.path"), "-proc:only"), null, sources);
        task.setProcessors(List.of(new GraphCheckProcessor()));
        System.out.println("javac succeeded: " + task.call());
        for (Diagnostic<? extends JavaFileObject> d : diagnostics.getDiagnostics()) {
            String file = d.getSource().getName().substring(d.getSource().getName().lastIndexOf('/') + 1);
            System.out.println(file + ":" + d.getLineNumber() + ": " + d.getKind().toString().toLowerCase() + ": " + d.getMessage(null));
        }
    }

    private static JavaFileObject source(String path, String text) {
        return new SimpleJavaFileObject(URI.create("string:///" + path), JavaFileObject.Kind.SOURCE) {
            @Override
            public CharSequence getCharContent(boolean ignoreEncodingErrors) {
                return text;
            }
        };
    }
}
