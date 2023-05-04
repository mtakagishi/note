sphinxで様々な数式を表現する
=====================================
以下のような複雑な数式を表現できます。 [#]_

.. math::

  W^{3\beta}_{\delta_1 \rho_1 \sigma_2} = U^{3\beta}_{\delta_1 \rho_1} + \frac{1}{8 \pi 2} \int^{\alpha_2}_{\alpha_2} d \alpha^\prime_2 \left[\frac{ U^{2\beta}_{\delta_1 \rho_1} - \alpha^\prime_2U^{1\beta}_{\rho_1 \sigma_2} }{U^{0\beta}_{\rho_1 \sigma_2}}\right]

上記数式の中身
  W^{3\\beta}_{\\delta_1 \\rho_1 \\sigma_2} = U^{3\\beta}_{\\delta_1 \\rho_1} + \\frac{1}{8 \\pi 2} \\int^{\\alpha_2}_{\\alpha_2} d \\alpha^\\prime_2 \\left[\\frac{ U^{2\\beta}_{\\delta_1 \\rho_1} - \\alpha^\\prime_2U^{1\\beta}_{\\rho_1 \\sigma_2} }{U^{0\\beta}_{\\rho_1 \\sigma_2}}\\right]


よく利用しそうな数式
-------------------------

分数
  frac
    f(x)=\\frac{分子}{分母}

.. math::

  f(x)=\frac{分子}{分母}

累乗
  W^{累乗}

.. math::
  W^{累乗}

ダッシュ
  W^{\\prime}

.. math::
  W^{\prime}

ギリシャ文字   [#]_
  \\alpha

.. math::
  \alpha

.. rubric:: 関連リンク

* .. [#] `Sample Doc Using math <https://matplotlib.org/sampledoc/extensions.html#using-math>`_ 
* .. [#] https://matplotlib.org/2.0.2/users/mathtext.html