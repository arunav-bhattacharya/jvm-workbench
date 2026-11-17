package workbench.container.l01.demo;

import workbench.container.l01.Container;
import workbench.container.l01.ContainerException;
import workbench.container.l01.demo.app.BoxOffice;

import java.util.List;

/** Wires the demo app from a scan, prints the creation order, then tries a graph with a cycle. */
public class GraphDemo {
    public static class Rota { public Rota(CastList cast) {} }                       // who works which night
    public static class CastList { public CastList(RehearsalPlan rehearsals) {} }
    public static class RehearsalPlan { public RehearsalPlan(Rota rota) {} }

    public static void main(String[] args) {
        Container app = Container.scan("workbench.container.l01.demo.app");
        System.out.println("creation order: " + app.creationOrder().stream().map(Class::getSimpleName).toList());
        app.get(BoxOffice.class).sell("C12", 12_000);

        try {
            new Container(List.of(Rota.class, CastList.class, RehearsalPlan.class));
        } catch (ContainerException e) {
            System.out.println("cycle: " + e.getMessage());
        }
    }
}
