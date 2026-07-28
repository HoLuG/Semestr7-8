package r5j;

public class Go_ extends r5jrt.Function {
  public Go_() {
    super(1, 1);
    goTo = 0;
  }

  private int[] e = new int[0];
  private r5jrt.Slice[] s = new r5jrt.Slice[1];

  @Override
  @SuppressWarnings("fallthrough")
  public void eval(r5jrt.Runtime runtime) {
    // e=e
    r5jrt.Function[] calls = new r5jrt.Function[2];
    for ( ; ; ) {
      switch (goTo) {
      case 0:
        s[0] = (r5jrt.Slice) args[0];
        goTo = 1;
        if (0 != s[0].getSize()) continue;
        calls[0] = new r5j.Go_.RangeUp_();
        calls[0].args[0] = r5jrt.Slice.concat(
          r5jrt.Slice.fromTerm(Integer.valueOf(1)),
          r5jrt.Slice.fromTerm(Integer.valueOf(500))
        );
        calls[1] = new r5j.Go_.Sum_();
        calls[0].returns[0] = new r5jrt.ReturnValue(calls[1].args, 0, calls[0].returns[0]);
        {
          calls[1].returns[0] = r5jrt.ReturnValue.join(calls[1].returns[0], returns[0]);
        }
        runtime.push(calls, 2);
        return;

      case 1:
        throw new r5jrt.RefalException(this);
      }
    }
  }

  public static class Sum_ extends r5jrt.Function {
    public Sum_() {
      super(1, 1);
      goTo = 0;
    }

    private int[] e = new int[0];
    private r5jrt.Slice[] s = new r5jrt.Slice[1];

    @Override
    @SuppressWarnings("fallthrough")
    public void eval(r5jrt.Runtime runtime) {
      // e=e
      r5jrt.Function[] calls = new r5jrt.Function[3];
      for ( ; ; ) {
        switch (goTo) {
        case 0:
          s[0] = (r5jrt.Slice) args[0];
          goTo = 1;
          if (0 != s[0].getSize()) continue;
          {
            r5jrt.Slice temp_e;
            temp_e = r5jrt.Slice.fromTerm(Integer.valueOf(0));
            r5jrt.ReturnValue.assign(returns[0], temp_e);
          }
          runtime.push(calls, 0);
          return;

        case 1:
          s[0] = (r5jrt.Slice) args[0];
          goTo = 2;
          if (0 >= s[0].getSize()) continue;
          // e.Rest â s[0].slice(1, s[0].getSize() - 1)
          // s.X
          if (s[0].at(0) instanceof r5jrt.Slice) continue;
          calls[0] = new r5j.Go_.Sum_();
          calls[0].args[0] = s[0].slice(1, s[0].getSize() - 1);
          calls[1] = new ExprFunction0();
          calls[1].args[0] = s[0].at(0);
          calls[0].returns[0] = new r5jrt.ReturnValue(calls[1].args, 1, calls[0].returns[0]);
          calls[2] = new r5j.Add_();
          calls[1].returns[0] = new r5jrt.ReturnValue(calls[2].args, 0, calls[1].returns[0]);
          {
            calls[2].returns[0] = r5jrt.ReturnValue.join(calls[2].returns[0], returns[0]);
          }
          runtime.push(calls, 3);
          return;

        case 2:
          throw new r5jrt.RefalException(this);
        }
      }
    }

    private static class ExprFunction0 extends r5jrt.ExprFunction {
      ExprFunction0() {
        super("s.#0 e.#1", 2);
      }

      @Override
      public r5jrt.Slice makeExpr() {
        return r5jrt.Slice.concat(
          r5jrt.Slice.fromTerm(args[0]),
          (r5jrt.Slice) args[1]
        );
      }
    }
  }

  public static class RangeUp_ extends r5jrt.Function {
    public RangeUp_() {
      super(1, 1);
      goTo = 0;
    }

    private int[] e = new int[0];
    private r5jrt.Slice[] s = new r5jrt.Slice[1];

    @Override
    @SuppressWarnings("fallthrough")
    public void eval(r5jrt.Runtime runtime) {
      // e=e
      r5jrt.Function[] calls = new r5jrt.Function[3];
      for ( ; ; ) {
        switch (goTo) {
        case 0:
          s[0] = (r5jrt.Slice) args[0];
          goTo = 1;
          if (2 != s[0].getSize()) continue;
          // s.From
          if (s[0].at(0) instanceof r5jrt.Slice) continue;
          // s.To
          if (s[0].at(1) instanceof r5jrt.Slice) continue;
          calls[0] = new r5j.Compare_();
          calls[0].args[0] = r5jrt.Slice.concat(
            r5jrt.Slice.fromTerm(s[0].at(0)),
            r5jrt.Slice.fromTerm(s[0].at(1))
          );
          calls[1] = new ExprFunction0();
          calls[0].returns[0] = new r5jrt.ReturnValue(calls[1].args, 0, calls[0].returns[0]);
          calls[1].args[1] = s[0].at(0);
          calls[1].args[2] = s[0].at(1);
          calls[2] = new r5j.Go_.ConsBy_();
          calls[1].returns[0] = new r5jrt.ReturnValue(calls[2].args, 0, calls[1].returns[0]);
          {
            calls[2].returns[0] = r5jrt.ReturnValue.join(calls[2].returns[0], returns[0]);
          }
          runtime.push(calls, 3);
          return;

        case 1:
          throw new r5jrt.RefalException(this);
        }
      }
    }

    private static class ExprFunction0 extends r5jrt.ExprFunction {
      ExprFunction0() {
        super("e.#0 s.#1 s.#2", 3);
      }

      @Override
      public r5jrt.Slice makeExpr() {
        return r5jrt.Slice.concat(
          (r5jrt.Slice) args[0],
          r5jrt.Slice.fromTerm(args[1]),
          r5jrt.Slice.fromTerm(args[2])
        );
      }
    }
  }

  public static class ConsBy_ extends r5jrt.Function {
    public ConsBy_() {
      super(1, 1);
      goTo = 0;
    }

    private int[] e = new int[0];
    private r5jrt.Slice[] s = new r5jrt.Slice[1];

    @Override
    @SuppressWarnings("fallthrough")
    public void eval(r5jrt.Runtime runtime) {
      // e=e
      r5jrt.Function[] calls = new r5jrt.Function[4];
      for ( ; ; ) {
        switch (goTo) {
        case 0:
          s[0] = (r5jrt.Slice) args[0];
          goTo = 1;
          if (3 != s[0].getSize()) continue;
          // s.From
          if (s[0].at(1) instanceof r5jrt.Slice) continue;
          // s.To
          if (s[0].at(2) instanceof r5jrt.Slice) continue;
          if (! (Character.valueOf('+').equals(s[0].at(0)))) continue;
          {
            r5jrt.Slice temp_e;
            temp_e = r5jrt.Slice.EMPTY;
            r5jrt.ReturnValue.assign(returns[0], temp_e);
          }
          runtime.push(calls, 0);
          return;

        case 1:
          s[0] = (r5jrt.Slice) args[0];
          goTo = 2;
          if (3 != s[0].getSize()) continue;
          // s.Op
          if (s[0].at(0) instanceof r5jrt.Slice) continue;
          // s.From
          if (s[0].at(1) instanceof r5jrt.Slice) continue;
          // s.To
          if (s[0].at(2) instanceof r5jrt.Slice) continue;
          calls[0] = new r5j.Add_();
          calls[0].args[0] = r5jrt.Slice.concat(
            r5jrt.Slice.fromTerm(s[0].at(1)),
            r5jrt.Slice.fromTerm(Integer.valueOf(1))
          );
          calls[1] = new ExprFunction0();
          calls[0].returns[0] = new r5jrt.ReturnValue(calls[1].args, 0, calls[0].returns[0]);
          calls[1].args[1] = s[0].at(2);
          calls[2] = new r5j.Go_.RangeUp_();
          calls[1].returns[0] = new r5jrt.ReturnValue(calls[2].args, 0, calls[1].returns[0]);
          calls[3] = new ExprFunction1();
          calls[3].args[0] = s[0].at(1);
          calls[2].returns[0] = new r5jrt.ReturnValue(calls[3].args, 1, calls[2].returns[0]);
          {
            calls[3].returns[0] = r5jrt.ReturnValue.join(calls[3].returns[0], returns[0]);
          }
          runtime.push(calls, 4);
          return;

        case 2:
          throw new r5jrt.RefalException(this);
        }
      }
    }

    private static class ExprFunction0 extends r5jrt.ExprFunction {
      ExprFunction0() {
        super("e.#0 s.#1", 2);
      }

      @Override
      public r5jrt.Slice makeExpr() {
        return r5jrt.Slice.concat(
          (r5jrt.Slice) args[0],
          r5jrt.Slice.fromTerm(args[1])
        );
      }
    }

    private static class ExprFunction1 extends r5jrt.ExprFunction {
      ExprFunction1() {
        super("s.#0 e.#1", 2);
      }

      @Override
      public r5jrt.Slice makeExpr() {
        return r5jrt.Slice.concat(
          r5jrt.Slice.fromTerm(args[0]),
          (r5jrt.Slice) args[1]
        );
      }
    }
  }

  public static class Mu_ extends r5jrt.meta.Mu_ {
    //e=e
    static final java.util.Map<String, Class<? extends r5jrt.Function>> table =
      new java.util.HashMap<>();

    @Override
    protected java.util.Map<String, Class<? extends r5jrt.Function>> getTable() {
      return table;
    }

    static {
      table.put("Go", r5j.Go_.class);
      table.put("Sum", r5j.Go_.Sum_.class);
      table.put("RangeUp", r5j.Go_.RangeUp_.class);
      table.put("ConsBy", r5j.Go_.ConsBy_.class);
      table.put("Mu", r5j.Go_.Mu_.class);
      table.put("Residue", r5j.Go_.Residue_.class);
      table.put("Up", r5j.Go_.Up_.class);
      table.put("Ev-met", r5j.Go_.Ev_mmet_.class);
    }
  }

  public static class Residue_ extends r5jrt.meta.Residue_ {
    //e=e
    @Override
    protected java.util.Map<String, Class<? extends r5jrt.Function>> getTable() {
      return Go_.Mu_.table;
    }
  }

  public static class Up_ extends r5jrt.meta.Up_ {
    //e=e
    @Override
    protected java.util.Map<String, Class<? extends r5jrt.Function>> getTable() {
      return Go_.Mu_.table;
    }
  }

  public static class Ev_mmet_ extends r5jrt.meta.Ev_mmet_ {
    //e=e
    @Override
    protected java.util.Map<String, Class<? extends r5jrt.Function>> getTable() {
      return Go_.Mu_.table;
    }
  }

  public static void main(String[] args) throws Exception {
    r5jrt.Runtime.run(new Go_(), args);
  }
}
