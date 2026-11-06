





:class:`README`
===============


.. py:class:: src.ansys.pre_commit_hooks.quality_rules.readme.README

   Bases: :py:obj:`abc.ABC`


   
   README rule family.

   Base class of the README quality rules. Each rule is a subclass named
   ``RM<nnn>`` with a static ``check`` method that receives the repository root
   and the name of the detected README file.















   ..
       !! processed by numpydoc !!



.. py:currentmodule:: README

Overview
--------

.. tab-set::

   .. tab-item:: Abstract methods

      .. list-table::
          :header-rows: 0
          :widths: auto

          * - :py:attr:`~check`
            - Evaluate a README rule.





   .. tab-item:: Attributes

      .. list-table::
          :header-rows: 0
          :widths: auto

          * - :py:attr:`~family`
            - 






Import detail
-------------

.. code-block:: python

    from src.ansys.pre_commit_hooks.quality_rules.readme import README


Attribute detail
----------------

.. py:attribute:: family
   :type:  ClassVar[str]
   :value: 'readme'




Method detail
-------------

.. py:method:: check(repository_root: pathlib.Path, readme_file: str | None) -> ansys.pre_commit_hooks.quality_rules.common.RuleCheckResult
   :staticmethod:

   :abstractmethod:


   
   Evaluate a README rule.


   :Parameters:

       **repository_root** : :obj:`pathlib.Path`
           Repository root directory.

       **readme_file** : :class:`python:str` or :data:`python:None`
           Detected README path, or ``None`` when no supported README exists.



   :Returns:

       :ref:`bool <python:bltin-boolean-values>` or :class:`python:str`
           Raw rule result consumed by the quality-report runner.











   ..
       !! processed by numpydoc !!




