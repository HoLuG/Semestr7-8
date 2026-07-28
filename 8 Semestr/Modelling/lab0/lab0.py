import numpy as np
import matplotlib.pyplot as plt


class RungeKuttaSolver:
    def __init__(self, dt=0.01):
        self.dt = dt
    
    def rk4_step(self, f, t, y):
        k1 = self.dt * f(t, y)
        k2 = self.dt * f(t + self.dt/2, y + k1/2)
        k3 = self.dt * f(t + self.dt/2, y + k2/2)
        k4 = self.dt * f(t + self.dt, y + k3)
        
        return y + (k1 + 2*k2 + 2*k3 + k4) / 6
    
    def solve(self, f, y0, t_span):
        y = np.zeros((len(t_span), len(y0)))
        y[0] = y0
        
        for i in range(1, len(t_span)):
            y[i] = self.rk4_step(f, t_span[i-1], y[i-1])
            
        return y


class GalileiModel:
    def __init__(self, g=9.81, v0=1.0, alpha=45.0):
        self.g = g
        self.v0 = v0
        self.alpha = np.deg2rad(alpha)
    
    def solve_numerically(self, t_span, dt=0.01):
        t_flight = 2.0 * self.v0 * np.sin(self.alpha) / self.g
        

        if len(t_span) > 0 and t_span[-1] < t_flight * 1.5:
            t_max = t_flight * 1.5
            t_span = np.arange(0, t_max, dt)
        x0 = 0.0
        y0 = 0.0
        u0 = self.v0 * np.cos(self.alpha)
        w0 = self.v0 * np.sin(self.alpha)
        
        y_init = np.array([x0, y0, u0, w0])
        
        def f_galilei(t, y):
            x, y_pos, u, w = y
            return np.array([u, w, 0, -self.g])
        
        solver = RungeKuttaSolver(dt=dt)
        solution = solver.solve(f_galilei, y_init, t_span)
        
        x = solution[:, 0]
        y = solution[:, 1]

        mask = y >= 0
        if not np.all(mask):
            first_negative = np.where(~mask)[0]
            if len(first_negative) > 0:
                mask = np.arange(len(y)) < first_negative[0]
        else:
            last_positive = np.where(y >= 0)[0]
            if len(last_positive) > 0:
                mask = np.arange(len(y)) <= last_positive[-1]
        
        return x[mask], y[mask]


class NewtonModel:
    def __init__(self, g=9.81, v0=1.0, alpha=45.0, m=None, r_core=None, rho_core=None, 
                 beta=None, C=0.15, rho_air=1.225, S=None):
        self.g = g
        self.v0 = v0
        self.alpha = np.deg2rad(alpha)
        
        if m is None:
            if r_core is None or rho_core is None:
                raise ValueError("Необходимо задать либо m, либо r_core и rho_core")
            V_core = (4.0 / 3.0) * np.pi * r_core**3
            self.m = rho_core * V_core
            self.r_core = r_core
            self.rho_core = rho_core
        else:
            self.m = m
            self.r_core = r_core
            self.rho_core = rho_core
        
        if S is None:
            if r_core is not None:
                self.S = np.pi * r_core**2
            else:
                raise ValueError("Необходимо задать либо S, либо r_core")
        else:
            self.S = S
        
        if beta is None:
            self.beta = C * rho_air * self.S / 2.0
        else:
            self.beta = beta
    
    def solve(self, t_span, dt=0.01):
        x0 = 0.0
        y0 = 0.0
        u0 = self.v0 * np.cos(self.alpha)
        w0 = self.v0 * np.sin(self.alpha)
        
        y_init = np.array([x0, y0, u0, w0])
        
        def f_newton(t, y):
            x, y_pos, u, w = y
            V = np.sqrt(u**2 + w**2)

            if V < 1e-10:
                du_dt = 0
                dw_dt = -self.g
            else:
                du_dt = -self.beta * u * V / self.m
                dw_dt = -self.g - self.beta * w * V / self.m
            
            return np.array([u, w, du_dt, dw_dt])
        
        solver = RungeKuttaSolver(dt=dt)
        solution = solver.solve(f_newton, y_init, t_span)
        
        x = solution[:, 0]
        y = solution[:, 1]
        u = solution[:, 2]
        w = solution[:, 3]
        
        mask = y >= 0
        return x[mask], y[mask], u[mask], w[mask]


def plot_trajectories(g=9.81, v0=30.0, alpha=45.0, C=0.5, rho_air=1.225, 
                      S=None, r_core=0.04, rho_core=200.0, diff_range=None, dt=0.001, 
                      filename='trajectory_comparison.png'):
    if S is None:
        S = np.pi * r_core**2
    
    t_flight_galilei = 2.0 * v0 * np.sin(np.deg2rad(alpha)) / g
    t_max = max(5.0, t_flight_galilei * 1.5)
    t_span = np.arange(0, t_max, dt)
    
    galilei = GalileiModel(g=g, v0=v0, alpha=alpha)
    x_gal, y_gal = galilei.solve_numerically(t_span, dt=dt)
    
    newton = NewtonModel(g=g, v0=v0, alpha=alpha, r_core=r_core, rho_core=rho_core, 
                         C=C, rho_air=rho_air)
    x_newt, y_newt, u_newt, w_newt = newton.solve(t_span, dt=dt)
    
    plt.figure(figsize=(8, 6))
    if len(x_gal) > 0 and len(y_gal) > 0:
        plt.plot(x_gal, y_gal, color='#0066CC', linestyle='-', linewidth=2.5, 
                label='Галилей', zorder=2)
        x_max_gal = np.max(x_gal)
        y_max_gal = np.max(y_gal)
        plt.xlim(-0.005, x_max_gal * 1.05)
        plt.ylim(-0.005, y_max_gal * 1.1)
        
        plt.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5, zorder=0)
        plt.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5, zorder=0)
    
    plt.xlabel('x (м)', fontsize=11)
    plt.ylabel('y (м)', fontsize=11)
    plt.title('Траектория Галилея\n(упрощенный Ньютон без сопротивления воздуха)', 
              fontsize=12, fontweight='bold')
    plt.legend(fontsize=9, loc='upper right', framealpha=0.9)
    plt.grid(True, alpha=0.3, linestyle=':')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig('trajectory_galilei.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    plt.figure(figsize=(8, 6))
    if len(x_newt) > 0 and len(y_newt) > 0:
        x_parabola = np.linspace(0, np.max(x_newt), 1000)
        y_parabola = -g / (2 * v0**2 * np.cos(np.deg2rad(alpha))**2) * x_parabola**2 + np.tan(np.deg2rad(alpha)) * x_parabola
        y_parabola = y_parabola[y_parabola >= 0]
        x_parabola = x_parabola[:len(y_parabola)]
        
        plt.plot(x_parabola, y_parabola, color='#00CCFF', linestyle='--', linewidth=1.5, 
                label='Парабола (для сравнения)', zorder=1, alpha=0.6)
        plt.plot(x_newt, y_newt, color='#CC0000', linestyle='-', linewidth=2.5, 
                label='Ньютон (непараболическая)', zorder=2)
        x_max_newt = np.max(x_newt)
        y_max_newt = np.max(y_newt)
        plt.xlim(-0.005, x_max_newt * 1.05)
        plt.ylim(-0.005, y_max_newt * 1.1)
        
        plt.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5, zorder=0)
        plt.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5, zorder=0)
    
    plt.xlabel('x (м)', fontsize=11)
    plt.ylabel('y (м)', fontsize=11)
    plt.title('Траектория Ньютона\n(с учетом сопротивления воздуха)', 
              fontsize=12, fontweight='bold')
    plt.legend(fontsize=9, loc='upper right', framealpha=0.9)
    plt.grid(True, alpha=0.3, linestyle=':')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig('trajectory_newton.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    plt.figure(figsize=(8, 6))
    if len(x_gal) > 0 and len(x_newt) > 0:
        if diff_range is None:
            range_gal = np.max(x_gal)
            range_newt = np.max(x_newt)
            diff_range = range_gal - range_newt
        else:
            range_gal = np.max(x_gal)
            range_newt = np.max(x_newt)
        
        t_gal = np.arange(0, len(x_gal)) * dt
        t_newt = np.arange(0, len(x_newt)) * dt
        
        t_min = 0
        t_max_common = min(t_gal[-1] if len(t_gal) > 0 else 0, t_newt[-1] if len(t_newt) > 0 else 0)
        t_common = np.linspace(t_min, t_max_common, 1000)
        
        x_gal_interp = np.interp(t_common, t_gal, x_gal)
        x_newt_interp = np.interp(t_common, t_newt, x_newt)
        
        diff_x = x_gal_interp - x_newt_interp
        
        plt.plot(x_gal_interp, diff_x, color='purple', linestyle='-', linewidth=2.5, 
                label='Разница по x (Галилей - Ньютон)', zorder=2)
        plt.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        
        plt.xlabel('x (м)', fontsize=11)
        plt.ylabel('Разница x (м)', fontsize=11)
        plt.title('Погрешность по дальности (x)', fontsize=12, fontweight='bold')
        plt.legend(fontsize=9, loc='best', framealpha=0.9)
        plt.grid(True, alpha=0.3, linestyle=':')
    
    plt.tight_layout()
    plt.savefig('trajectory_error.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    plt.figure(figsize=(8, 6))
    if len(x_gal) > 0 and len(x_newt) > 0:
        plt.plot(x_gal, y_gal, color='#0066CC', linestyle='-', linewidth=2.5, 
                label='Галилей', zorder=2)
        plt.plot(x_newt, y_newt, color='#CC0000', linestyle='-', linewidth=2.5, 
                label='Ньютон', zorder=3)
        plt.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5, zorder=0)
        plt.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5, zorder=0)
        
        x_max = max(np.max(x_gal), np.max(x_newt))
        y_max = max(np.max(y_gal), np.max(y_newt))
        plt.xlim(-0.005, x_max * 1.05)
        plt.ylim(-0.005, y_max * 1.1)
    
    plt.xlabel('x (м)', fontsize=11)
    plt.ylabel('y (м)', fontsize=11)
    plt.title('Сравнение траекторий', fontsize=12, fontweight='bold')
    plt.legend(fontsize=9, loc='upper right', framealpha=0.9)
    plt.grid(True, alpha=0.3, linestyle=':')
    
    plt.tight_layout()
    plt.savefig('trajectory_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()


if __name__ == "__main__":
    g = 9.81
    v0 = 60.0
    alpha = 43.0
    C = 0.15
    rho_air = 1.225
    r_core = 0.04
    rho_core = 7300.0
    
    S = np.pi * r_core**2
    V_core = (4.0 / 3.0) * np.pi * r_core**3
    m = rho_core * V_core
    beta = C * rho_air * S / 2.0
    
    t_flight_galilei = 2.0 * v0 * np.sin(np.deg2rad(alpha)) / g
    t_max = max(1.0, t_flight_galilei * 1.5)
    dt = 0.001
    t_span = np.arange(0, t_max, dt)
    
    print("=" * 60)
    print("ВХОДНЫЕ ПАРАМЕТРЫ")
    print("=" * 60)
    print(f"  g = {g} m/s^2")
    print(f"  v0 = {v0} m/s")
    print(f"  alpha = {alpha} grad")
    print(f"  C = {C}")
    print(f"  rho_air = {rho_air} kg/m^3")
    print(f"  S = {S} m^2 ({S*100:.1f} dm^2 = {S*10000:.0f} cm^2)")
    print(f"  rho_core = {rho_core} kg/m^3")
    
    print("\n" + "=" * 60)
    print("ВЫЧИСЛЯЕМЫЕ ПАРАМЕТРЫ")
    print("=" * 60)
    print(f"  r_core = sqrt(S/pi) = {r_core:.6f} m")
    print(f"  V_core = (4/3)*pi*r^3 = {V_core:.6f} m^3")
    print(f"  m = rho_core * V_core = {m:.6f} kg")
    print(f"  beta = C*rho_air*S/2 = {beta:.6f}")
    print(f"  t_flight (Galilei) = 2*v0*sin(alpha)/g = {t_flight_galilei:.4f} s")
    print(f"  t_max = {t_max:.4f} s")
    print(f"  dt = {dt} s")
    
    print("\n" + "=" * 60)
    print("Модель Галилея (упрощенный Ньютон без сопротивления воздуха)")
    print("=" * 60)
    galilei = GalileiModel(g=g, v0=v0, alpha=alpha)
    x_gal, y_gal = galilei.solve_numerically(t_span, dt=dt)
    range_gal = np.max(x_gal)
    print(f"Дальность полёта: {range_gal:.4f} m")
    
    print("\n" + "=" * 60)
    print("Модель Ньютона (с учетом сопротивления воздуха)")
    print("=" * 60)
    newton = NewtonModel(g=g, v0=v0, alpha=alpha, r_core=r_core, rho_core=rho_core, 
                         C=C, rho_air=rho_air)
    x_newt, y_newt, u_newt, w_newt = newton.solve(t_span, dt=dt)
    range_newt = np.max(x_newt)
    print(f"Дальность полёта: {range_newt:.4f} m")

    print("\n" + "=" * 60)
    print("СРАВНЕНИЕ ДАЛЬНОСТИ ПОЛЁТА")
    print("=" * 60)
    diff_range = range_gal - range_newt
    
    print(f"Разница в дальности: {diff_range:.6f} m ({diff_range*1000:.3f} mm)")
    
    relative_error = abs(diff_range / range_gal) * 100
    print(f"Относительная погрешность: {relative_error:.6f} %")
    

    plot_trajectories(g=g, v0=v0, alpha=alpha, C=C, rho_air=rho_air, 
                     S=S, r_core=r_core, rho_core=rho_core, 
                     diff_range=diff_range, dt=dt)

