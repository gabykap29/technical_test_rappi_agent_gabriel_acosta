declare module "react-plotly.js" {
  import type { ComponentType, CSSProperties } from "react";

  type PlotProps = {
    data?: unknown[];
    layout?: Record<string, unknown>;
    config?: Record<string, unknown>;
    style?: CSSProperties;
    useResizeHandler?: boolean;
  };

  const Plot: ComponentType<PlotProps>;
  export default Plot;
}
